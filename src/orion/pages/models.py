"""Orion's page types, and the categories and tags that classify articles."""

import datetime

from django import forms
from django.conf import settings
from django.contrib.syndication.views import Feed
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import models
from django.http import Http404
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    MultipleChooserPanel,
)
from wagtail.contrib.routable_page.models import RoutablePageMixin, path
from wagtail.coreutils import cautious_slugify
from wagtail.fields import StreamField
from wagtail.models import (
    Locale,
    Orderable,
    Page,
    PageManager,
    Site,
    TranslatableMixin,
)
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail_localize.fields import SynchronizedField

from orion.core.blocks import BodyStreamField, ContentStreamBlock, SiteStreamBlock
from orion.core.blocks.content import is_visible
from orion.core.images import get_leading_hero_image
from orion.seo.models import SeoMixin

DEFAULT_ARTICLES_PER_PAGE = 12
DEFAULT_FEED_ITEMS = 20


class ArticleStreamBlock(ContentStreamBlock):
    """The body of an article: an article has its own header, so no hero."""

    hero = None
    latest_articles = None


class DesktopPreviewMixin:
    """Opens the editor's preview at desktop size, as sites are mostly built for it."""

    @property
    def default_preview_size(self):
        return "desktop"


class BodyPage(SeoMixin, DesktopPreviewMixin, Page):
    """A page whose content is a body of Orion's content blocks."""

    body = BodyStreamField(SiteStreamBlock(), blank=True, verbose_name=_("body"))

    content_panels = [*Page.content_panels, FieldPanel("body")]
    search_fields = [*SeoMixin.search_fields, index.SearchField("body")]

    class Meta:
        abstract = True

    def get_social_image(self):
        return super().get_social_image() or get_leading_hero_image(self)

    @property
    def starts_with_hero(self):
        """Whether the first visible block is a hero, which then holds the h1."""
        first_block = next(
            (block for block in self.body if is_visible(block.value)), None
        )
        return first_block is not None and first_block.block_type == "hero"


class HomePage(BodyPage):
    parent_page_types = ["wagtailcore.Page"]
    template = "orion/pages/home_page.html"

    class Meta:
        verbose_name = _("home page")
        verbose_name_plural = _("home pages")

    @classmethod
    def can_create_at(cls, parent):
        # One home page per site. Translations are created by wagtail-localize, which
        # does not go through this check, so each language still gets its own.
        return super().can_create_at(parent) and not cls.objects.exists()


class ContentPage(BodyPage):
    parent_page_types = ["orion_pages.HomePage", "orion_pages.ContentPage"]
    template = "orion/pages/content_page.html"

    class Meta:
        verbose_name = _("content page")
        verbose_name_plural = _("content pages")


class ContactPage(BodyPage):
    parent_page_types = ["orion_pages.HomePage", "orion_pages.ContentPage"]
    subpage_types = []
    template = "orion/pages/contact_page.html"

    class Meta:
        verbose_name = _("contact page")
        verbose_name_plural = _("contact pages")

    def get_context(self, request, *args, **kwargs):
        # Imported here like in the contact block: settings load after page models.
        from orion.site_data.models import SiteSettings

        context = super().get_context(request, *args, **kwargs)
        site_settings = SiteSettings.load(request_or_site=request)
        context["site_items"] = site_settings.contact_items()
        site = Site.find_for_request(request)
        site_point = site_settings.map_point(name=site.site_name if site else "")
        context["map_points"] = [site_point] if site_point else []
        context["map_zoom"] = site_settings.map_zoom
        return context


class TaxonomyMixin(TranslatableMixin, models.Model):
    """A translatable name with a slug for URLs, unique within its language."""

    name = models.CharField(_("name"), max_length=100)
    slug = models.SlugField(
        _("slug"),
        max_length=100,
        blank=True,
        allow_unicode=True,
        help_text=_("Used in filter URLs. Leave empty to build it from the name."),
    )

    class Meta(TranslatableMixin.Meta):
        abstract = True

    def clean(self):
        super().clean()
        allow_unicode = getattr(settings, "WAGTAIL_ALLOW_UNICODE_SLUGS", True)
        if not self.slug:
            # Names without Latin letters slugify to nothing in ASCII; Wagtail's
            # cautious_slugify escapes them instead.
            self.slug = slugify(self.name, allow_unicode=allow_unicode) or (
                cautious_slugify(self.name)
            )
        elif not allow_unicode and not self.slug.isascii():
            raise ValidationError(
                {"slug": _("Use only letters without accents, numbers and hyphens.")}
            )

    @classmethod
    def from_slug(cls, slug):
        """Return the item with this slug in the active language, or the base one's."""
        for locale in (Locale.get_active(), Locale.get_default()):
            item = cls.objects.filter(slug=slug, locale=locale).first()
            if item is not None:
                return item
        return None


@register_snippet
class ArticleCategory(TaxonomyMixin):
    parent = models.ForeignKey(
        "self",
        verbose_name=_("parent category"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        limit_choices_to={"parent__isnull": True},
        help_text=_("Optional. Categories have two levels."),
    )

    panels = [FieldPanel("name"), FieldPanel("slug"), FieldPanel("parent")]

    class Meta(TaxonomyMixin.Meta):
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "locale"],
                name="orion_category_slug_per_locale",
                violation_error_message=_(
                    "This language already has a category with this slug."
                ),
            ),
        ]

    def __str__(self):
        return f"{self.parent.name} › {self.name}" if self.parent_id else self.name

    def clean(self):
        super().clean()
        if self.parent_id is None:
            return
        if self.parent_id == self.pk or self.parent.parent_id is not None:
            raise ValidationError(
                {"parent": _("Choose a category without a parent category.")}
            )
        if self.pk and self.children.exists():
            raise ValidationError(
                {"parent": _("This category has subcategories, so it cannot have one.")}
            )
        if self.locale_id and self.parent.locale_id != self.locale_id:
            raise ValidationError(
                {"parent": _("Choose a category in the same language.")}
            )

    @property
    def family_translation_keys(self):
        """This category's and its subcategories' translation keys, for filters."""
        child_keys = ArticleCategory.objects.filter(
            parent__translation_key=self.translation_key
        ).values_list("translation_key", flat=True)
        return {self.translation_key, *child_keys}


@register_snippet
class ArticleTag(TaxonomyMixin):
    panels = [FieldPanel("name"), FieldPanel("slug")]

    class Meta(TaxonomyMixin.Meta):
        verbose_name = _("tag")
        verbose_name_plural = _("tags")
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "locale"],
                name="orion_tag_slug_per_locale",
                violation_error_message=_(
                    "This language already has a tag with this slug."
                ),
            ),
        ]

    def __str__(self):
        return self.name


class ArticleIndexPage(SeoMixin, DesktopPreviewMixin, RoutablePageMixin, Page):
    intro = models.TextField(_("introduction"), blank=True, max_length=500)

    content_panels = [*Page.content_panels, FieldPanel("intro")]
    search_fields = [*SeoMixin.search_fields, index.SearchField("intro")]
    parent_page_types = ["orion_pages.HomePage", "orion_pages.ContentPage"]
    subpage_types = ["orion_pages.ArticlePage"]
    template = "orion/pages/article_index_page.html"

    class Meta:
        verbose_name = _("article listing")
        verbose_name_plural = _("article listings")

    def get_articles(self):
        return ArticlePage.objects.latest(index=self)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        articles = self.get_articles()
        category = tag = None
        if category_slug := request.GET.get("category"):
            category = ArticleCategory.from_slug(category_slug)
            if category is None:
                raise Http404
            articles = articles.filter(
                categories__translation_key__in=category.family_translation_keys
            ).distinct()
        if tag_slug := request.GET.get("tag"):
            tag = ArticleTag.from_slug(tag_slug)
            if tag is None:
                raise Http404
            articles = articles.filter(
                article_tags__tag__translation_key=tag.translation_key
            ).distinct()
        per_page = getattr(
            settings, "ORION_ARTICLES_PER_PAGE", DEFAULT_ARTICLES_PER_PAGE
        )
        context["articles"] = Paginator(articles, per_page).get_page(
            request.GET.get("page")
        )
        context["active_category"] = category
        context["active_tag"] = tag
        return context

    @path("rss/", name="feed")
    def feed(self, request):
        return ArticleFeed(self)(request)


class ArticlePageManager(PageManager):
    def latest(self, index=None, limit=None):
        """Published articles in the active language, newest first.

        With ``index``, only that listing's; the listing must already be in the active
        language (use ``index.localized``).
        """
        articles = (
            self.live()
            .filter(locale=index.locale if index else Locale.get_active())
            .order_by("-date", "-first_published_at")
            .select_related("image")
            .prefetch_related("categories", "article_tags__tag")
        )
        if index is not None:
            articles = articles.child_of(index)
        return articles[:limit] if limit else articles


class ArticlePageForm(WagtailAdminPageForm):
    """Offers only the categories of the article's language."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        locale_id = self.instance.locale_id or getattr(
            self.parent_page, "locale_id", None
        )
        if "categories" in self.fields and locale_id:
            self.fields["categories"].queryset = (
                ArticleCategory.objects.filter(locale_id=locale_id)
                .select_related("parent")
                .order_by(
                    models.functions.Coalesce("parent__name", "name"), "parent", "name"
                )
            )


class ArticlePage(SeoMixin, DesktopPreviewMixin, Page):
    date = models.DateField(_("date"), default=timezone.localdate)
    summary = models.TextField(
        _("summary"),
        max_length=300,
        help_text=_("Shown in listings and in the RSS feed."),
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("image"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    image_alt = models.CharField(
        _("alternative text"),
        max_length=255,
        blank=True,
        help_text=_("Describe the image for people who cannot see it."),
    )
    image_is_decorative = models.BooleanField(
        _("decorative image"),
        default=False,
        help_text=_("Check only if the image adds nothing to the text."),
    )
    categories = ParentalManyToManyField(
        ArticleCategory,
        verbose_name=_("categories"),
        blank=True,
        related_name="articles",
    )
    body = StreamField(ArticleStreamBlock(), blank=True, verbose_name=_("body"))

    objects = ArticlePageManager()

    content_panels = [
        *Page.content_panels,
        FieldPanel("date"),
        FieldPanel("summary"),
        MultiFieldPanel(
            [
                FieldPanel("image"),
                FieldPanel("image_alt"),
                FieldPanel("image_is_decorative"),
            ],
            heading=_("Image"),
        ),
        FieldPanel("categories", widget=forms.CheckboxSelectMultiple),
        MultipleChooserPanel("article_tags", chooser_field_name="tag", label=_("Tags")),
        FieldPanel("body"),
    ]
    search_fields = [
        *SeoMixin.search_fields,
        index.SearchField("summary"),
        index.SearchField("body"),
    ]
    base_form_class = ArticlePageForm
    # wagtail-localize skips many-to-many fields; translations keep the original's.
    override_translatable_fields = [SynchronizedField("categories")]
    parent_page_types = ["orion_pages.ArticleIndexPage"]
    subpage_types = []
    template = "orion/pages/article_page.html"
    og_type = "article"

    class Meta:
        verbose_name = _("article")
        verbose_name_plural = _("articles")

    def clean(self):
        super().clean()
        if self.image_id and not self.image_alt and not self.image_is_decorative:
            raise ValidationError(
                {
                    "image_alt": _(
                        "Describe the image, or mark it as decorative if it adds "
                        "nothing to the text."
                    )
                }
            )

    def get_meta_description(self):
        return super().get_meta_description() or self.summary

    def get_social_image(self):
        return super().get_social_image() or self.image

    @property
    def image_alt_text(self):
        """The image's alternative text; empty when it is decorative."""
        return "" if self.image_is_decorative else self.image_alt

    @property
    def tags(self):
        return [article_tag.tag for article_tag in self.article_tags.all()]


class ArticlePageTag(Orderable):
    page = ParentalKey(
        ArticlePage, on_delete=models.CASCADE, related_name="article_tags"
    )
    tag = models.ForeignKey(
        ArticleTag, verbose_name=_("tag"), on_delete=models.CASCADE, related_name="+"
    )

    panels = [FieldPanel("tag")]

    class Meta(Orderable.Meta):
        verbose_name = _("tag")
        verbose_name_plural = _("tags")


class ArticleFeed(Feed):
    """The latest articles of a listing, in the listing's language."""

    def __init__(self, index):
        super().__init__()
        self.index = index

    def title(self):
        return self.index.title

    def link(self):
        return self.index.url

    def description(self):
        return self.index.intro or self.index.title

    def items(self):
        return self.index.get_articles()[
            : getattr(settings, "ORION_FEED_ITEMS", DEFAULT_FEED_ITEMS)
        ]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return timezone.make_aware(
            datetime.datetime.combine(item.date, datetime.time())
        )

    def item_categories(self, item):
        return [category.localized.name for category in item.categories.all()]

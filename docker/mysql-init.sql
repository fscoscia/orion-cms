-- Lets the local test user create and drop the database used by the test suite.
GRANT ALL PRIVILEGES ON `test_orion`.* TO 'orion'@'%';
FLUSH PRIVILEGES;

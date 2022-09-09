-- migrate:up
CREATE database k3s;
CREATE user 'rancher'@'%' IDENTIFIED BY 'password' ACCOUNT LOCK;
GRANT ALL on k3s.* TO 'rancher'@'%';

-- migrate:down
DROP DATABASE k3s;
DROP USER rancher;

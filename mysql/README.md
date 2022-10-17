# MySQL
MySQL is the relational database of choice for the CSET team. This is where we store our schemas/definitions.

## Working with dbmate
`dbmate` allows us to version control our MySQL configuration and ensure we have a deployment/rollback plan. Detailed documentation can be found [here](https://github.com/amacneil/dbmate), but there are a few commands you should know. To create a new migration file, use `dbmate new <migration name>`. To apply pending migrations you run `dbmate migrate` and to rollback you run `dbmate rollback`. You do need to have the connection string available via `export DATABASE_URL="mysql://user:password@hostname:3306/mysql"`.

## Cluster Access
You can access the connection string in the CICD account secret `/KeePass/mysql/p3/dev`.

## Configuring Users
You can create a user via the dbmate configuration, but we can not store the password in plain text. To unlock and configure the password, you can use this command.
```sh
mysql -u sau_cset --password -h 10.32.154.155 -P 3306 -D mysql -e "ALTER USER rancher IDENTIFIED BY '<changeme>' ACCOUNT UNLOCK;"
```

FROM php:8.3-apache

COPY web-php/apache.conf /etc/apache2/sites-available/000-default.conf
COPY web-php /var/www/app
COPY web-angular/src/assets/data /var/www/data

RUN a2enmod rewrite \
    && echo "memory_limit=512M" > /usr/local/etc/php/conf.d/memory-limit.ini \
    && echo "ServerName localhost" > /etc/apache2/conf-available/servername.conf \
    && a2enconf servername

ENV CORPUS_DATA_DIR=/var/www/data
WORKDIR /var/www/app

EXPOSE 80

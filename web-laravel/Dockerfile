FROM composer:2 AS vendor
WORKDIR /app

COPY web-laravel/composer.json web-laravel/composer.lock ./
RUN composer install --no-dev --optimize-autoloader --no-interaction --no-scripts

FROM php:8.4-apache

COPY web-laravel/apache.conf /etc/apache2/sites-available/000-default.conf
COPY web-laravel /var/www/app
COPY --from=vendor /app/vendor /var/www/app/vendor
COPY web-angular/src/assets/data /var/www/data

RUN a2enmod rewrite \
    && echo "memory_limit=512M" > /usr/local/etc/php/conf.d/memory-limit.ini \
    && echo "ServerName localhost" > /etc/apache2/conf-available/servername.conf \
    && a2enconf servername \
    && mkdir -p /var/www/app/storage/framework/cache /var/www/app/storage/framework/views /var/www/app/storage/framework/sessions /var/www/app/bootstrap/cache \
    && chown -R www-data:www-data /var/www/app/storage /var/www/app/bootstrap/cache

ENV APP_ENV=production \
    APP_DEBUG=false \
    APP_KEY=base64:XCL4lKeiLpB99lwRy3ahhWs03jGdrEjmhhbZw/XTJh0= \
    APP_URL=http://localhost \
    LOG_CHANNEL=stderr \
    SESSION_DRIVER=file \
    CACHE_STORE=file \
    QUEUE_CONNECTION=sync \
    CORPUS_DATA_DIR=/var/www/data

WORKDIR /var/www/app
EXPOSE 80

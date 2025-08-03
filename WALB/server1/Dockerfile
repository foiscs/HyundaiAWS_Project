FROM php:8.1-apache

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libzip-dev \
    libonig-dev \
    libxml2-dev \
    libpq-dev \
    unzip \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# PHP 확장 모듈 설치
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
    gd \
    pdo \
    pdo_mysql \
    mysqli \
    mbstring \
    xml \
    zip \
    opcache

# Apache 모듈 활성화
RUN a2enmod rewrite headers

# Composer 설치
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# 작업 디렉토리 설정
WORKDIR /var/www/html

# Composer 의존성 설치
COPY composer.json composer.lock* ./
RUN composer install --no-dev --optimize-autoloader --no-interaction || \
    composer install --no-dev --optimize-autoloader --no-interaction --ignore-platform-reqs

# 애플리케이션 코드 복사
COPY files/app/ ./app/
COPY files/css/ ./app/css/
COPY files/simple-health.php ./app/
COPY files/health.php ./app/
COPY files/detailed-health.php ./app/
COPY files/db_test.php ./app/

# DocumentRoot 설정
ENV APACHE_DOCUMENT_ROOT=/var/www/html/app
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf
RUN sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

# 권한 설정
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html
# PHP 최적화 설정
RUN echo "upload_max_filesize = 10M" > /usr/local/etc/php/conf.d/optimization.ini \
    && echo "post_max_size = 10M" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "memory_limit = 256M" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "max_execution_time = 30" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "date.timezone = Asia/Seoul" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "# Database connection optimization" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "pdo.dsn.* = mysql:host=walb-mysql-rds.cx02kko4cplr.ap-northeast-2.rds.amazonaws.com" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "default_socket_timeout = 10" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "# OPcache settings for performance" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "opcache.enable = 1" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "opcache.memory_consumption = 128" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "opcache.max_accelerated_files = 4000" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "opcache.revalidate_freq = 60" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "opcache.fast_shutdown = 1" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "# DNS cache optimization" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "realpath_cache_size = 32M" >> /usr/local/etc/php/conf.d/optimization.ini \
    && echo "realpath_cache_ttl = 600" >> /usr/local/etc/php/conf.d/optimization.ini

EXPOSE 80

CMD ["apache2-foreground"]
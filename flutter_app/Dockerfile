FROM ghcr.io/cirruslabs/flutter:stable AS build
WORKDIR /app

COPY pubspec.yaml ./
COPY analysis_options.yaml ./
COPY lib ./lib
COPY assets ./assets

# If the local Flutter skeleton has not been generated yet, create only the web platform files.
RUN flutter config --enable-web \
    && flutter create --platforms=web --project-name relacion_formas_verbais_flutter . \
    && flutter pub get \
    && flutter build web --release

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build/web /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

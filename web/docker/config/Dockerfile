# Use a imagem oficial do Nginx baseada em Alpine (super leve ~40MB)
FROM nginx:alpine

# Remove a configuração padrão do Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copia nossa configuração customizada
# IMPORTANTE: Este comando assume que o build é executado da raiz do projeto (IFC5-development)
COPY docker/config/nginx.conf /etc/nginx/conf.d/default.conf

# Copia os arquivos estáticos do visualizador para o diretório padrão do Nginx
# COPY web/viewer /usr/share/nginx/html

# Expõe a porta 80
EXPOSE 80

# O comando padrão do nginx:alpine já inicia o servidor em foreground
CMD ["nginx", "-g", "daemon off;"]

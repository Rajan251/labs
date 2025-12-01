# my-app-repo/Dockerfile
FROM openjdk:11-jre-slim
COPY target/myapp.jar /app/myapp.jar
ENTRYPOINT ["java", "-jar", "/app/myapp.jar"]

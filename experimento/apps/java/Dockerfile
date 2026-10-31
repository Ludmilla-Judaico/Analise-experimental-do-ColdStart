FROM eclipse-temurin:17-jdk AS build
ARG WORKLOAD=minimal
WORKDIR /src
RUN mkdir lib
RUN if [ "$WORKLOAD" = "deps" ]; then cd lib && for j in jackson-core jackson-annotations jackson-databind; do \
      curl -fsSLO https://repo1.maven.org/maven2/com/fasterxml/jackson/core/$j/2.17.2/$j-2.17.2.jar; done; fi
COPY src/${WORKLOAD}/App.java .
RUN javac -cp "lib/*" -d out App.java

FROM eclipse-temurin:17-jre
COPY --from=build /src/out /app
COPY --from=build /src/lib /app/lib
CMD ["java", "-cp", "/app:/app/lib/*", "App"]
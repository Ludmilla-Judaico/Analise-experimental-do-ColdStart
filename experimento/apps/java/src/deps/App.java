import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class App {
    public static void main(String[] args) throws Exception {
        HttpServer s = HttpServer.create(new InetSocketAddress(8080), 0);
        s.createContext("/", e -> {
            byte[] b = "OK".getBytes();
            e.sendResponseHeaders(200, b.length);
            e.getResponseBody().write(b);
            e.close();
        });
        var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        var node = mapper.readTree("{\"a\":1,\"b\":[1,2,3]}");
        java.security.MessageDigest.getInstance("SHA-256").digest(node.toString().getBytes());
        java.net.http.HttpClient.newHttpClient();
        
        s.start();
    }
}
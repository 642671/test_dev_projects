
import java.net.URI;
import java.net.http.*;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;
import javax.crypto.Cipher;

public class RsaProbe {
    static PublicKey parse(String xRsaToken) throws Exception {
        String pem = new String(Base64.getDecoder().decode(xRsaToken));
        String b64 = pem.replaceAll("-----[^-]+-----", "").replaceAll("\\s", "");
        byte[] der = Base64.getDecoder().decode(b64);
        KeyFactory kf = KeyFactory.getInstance("RSA");
        return kf.generatePublic(new X509EncodedKeySpec(der));
    }
    static String encrypt(String plain, PublicKey pub) throws Exception {
        Cipher c = Cipher.getInstance("RSA/ECB/PKCS1Padding");
        c.init(Cipher.ENCRYPT_MODE, pub);
        byte[] out = c.doFinal(plain.getBytes("UTF-8"));
        return Base64.getEncoder().encodeToString(out);
    }
    static String get(String host, int port, String path) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest req = HttpRequest.newBuilder().uri(URI.create("http://"+host+":"+port+path)).GET().build();
        HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
        return resp.statusCode() + " | set-cookie=" + (resp.headers().firstValue("set-cookie").orElse("").length()) + " | xrsa=" + (resp.headers().firstValue("x-rsa-token").orElse("").length());
    }
    static String cookieVal(String sc, String name) { if(sc==null)return ""; for(String p:sc.split(";")){p=p.trim();int i=p.indexOf("=");if(i>0&&p.substring(0,i).equals(name))return p.substring(i+1);} return ""; }
    static String getSet(String host,int port,String path) throws Exception {
        HttpClient c=HttpClient.newHttpClient(); HttpRequest r=HttpRequest.newBuilder().uri(URI.create("http://"+host+":"+port+path)).GET().build();
        HttpResponse<String> s=c.send(r,HttpResponse.BodyHandlers.ofString()); return s.headers().firstValue("set-cookie").orElse("");
    }
    static String getRsa(String host,int port,String path) throws Exception {
        HttpClient c=HttpClient.newHttpClient(); HttpRequest r=HttpRequest.newBuilder().uri(URI.create("http://"+host+":"+port+path)).GET().build();
        HttpResponse<String> s=c.send(r,HttpResponse.BodyHandlers.ofString()); return s.headers().firstValue("x-rsa-token").orElse("");
    }
    static String post(String host,int port,String path,String csrf,String body,String cookie) throws Exception {
        HttpClient c=HttpClient.newHttpClient();
        HttpRequest.Builder rb=HttpRequest.newBuilder().uri(URI.create("http://"+host+":"+port+path)).header("Content-Type","application/json").header("X-Csrf-Token",csrf);
        if(cookie!=null)rb.header("Cookie",cookie);
        rb.POST(HttpRequest.BodyPublishers.ofString(body));
        HttpResponse<String> s=c.send(rb.build(),HttpResponse.BodyHandlers.ofString());
        return s.statusCode()+" | "+s.body().replaceAll("\\s+"," ").substring(0, Math.min(120, s.body().length()));
    }
    public static void main(String[] a) throws Exception {
        String host="10.18.15.135"; int port=8181;
        System.out.println("LANG "+ get(host,port,"/v2/lang/tos"));
        System.out.println("WEL "+ get(host,port,"/v2/welcome"));
        String langSc=getSet(host,port,"/v2/lang/tos");
        String csrf=cookieVal(langSc,"X-Csrf-Token");
        String rsa=getRsa(host,port,"/v2/welcome");
        PublicKey pub=parse(rsa);
        String enc=encrypt("Admin123",pub);
        System.out.println("ENC_LEN "+enc.length());
        String body="{\"username\":\"test\",\"password\":\""+enc+"\",\"code\":\"\",\"remember\":true,\"slidecode\":1}";
        System.out.println("LOGIN "+ post(host,port,"/v2/login",csrf,body,"X-Csrf-Token="+csrf));
    }
}

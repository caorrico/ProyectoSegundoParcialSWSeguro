import java.io.*;

public class DeserializationDemo {
    public static void main(String[] args) {
        try {
            // Read untrusted data from a file (or network)
            FileInputStream fileIn = new FileInputStream("untrusted_data.ser");
            
            // VULNERABILITY: Insecure Deserialization
            // Reads an object directly from the stream without verifying its class type.
            // An attacker can craft a malicious gadget chain.
            ObjectInputStream in = new ObjectInputStream(fileIn);
            Object obj = in.readObject();
            
            in.close();
            fileIn.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}

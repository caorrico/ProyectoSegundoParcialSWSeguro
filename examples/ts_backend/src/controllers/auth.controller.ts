import { Request, Response } from 'express';
import { db } from '../database'; // Simulated DB module

export class AuthController {
    
    // VULNERABLE ENDPOINT: NoSQL/SQL Injection
    public async login(req: Request, res: Response) {
        const username = req.body.username;
        const password = req.body.password;
        
        try {
            // BAD: User input passed directly into query without sanitization/parameterization
            const query = `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`;
            const user = await db.query(query);
            
            if (user) {
                // BAD: Hardcoded secret key for JWT token
                const token = jwt.sign({ id: user.id }, "my_super_secret_key_123");
                res.status(200).json({ success: true, token });
            } else {
                res.status(401).json({ success: false, message: "Invalid credentials" });
            }
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    }
}

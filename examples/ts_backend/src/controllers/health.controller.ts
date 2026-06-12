import { Request, Response } from 'express';

export class HealthController {
    
    // SAFE ENDPOINT
    public getHealth(req: Request, res: Response) {
        const uptime = process.uptime();
        const memory = process.memoryUsage();
        
        // No user inputs handled here
        res.status(200).json({
            status: 'success',
            message: 'API is running normally',
            uptime: uptime,
            metrics: {
                heapUsed: memory.heapUsed,
                heapTotal: memory.heapTotal
            }
        });
    }
}

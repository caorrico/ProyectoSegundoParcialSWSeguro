import express from 'express';

const app = express();

app.get('/search', (req, res) => {
    // VULNERABILITY: Reflected XSS
    // User input from req.query is sent directly back in the HTML response
    const searchTerm = req.query.q;
    
    // BAD: No sanitization
    res.send(`<h1>Results for: ${searchTerm}</h1><p>No results found.</p>`);
});

app.listen(3000);

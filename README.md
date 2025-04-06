# command_injection
Command Injection vulnerabilities occur when user-controlled input is improperly validated and executed as system commands
Loads payloads from external files in a payloads/ directory.

Randomizes headers and payload obfuscation to bypass detection (WAF/IPS).

Supports proxying (like Burp Suite) or TOR routing.

Accepts target URLs and parameters from a targets.txt file or manual input.

Detects command injection based on response content or timing behavior.

Logs:

    All results in scan_results.json

    Successful findings in successful_injections.json

    Errors in error_log.json

Sends a callback to an out-of-band (OOB) listener to log blind command injection.

Uses multi-threading for faster scanning.

python commandinjection.py

Enter parameters to test (comma-separated): search,query


Use a Different OOB Service

You can use Burp Collaborator or CanaryTokens for testing:

    Burp Collaborator: Generate a unique Collaborator URL from Burp Suite.

    CanaryTokens: Use https://canarytokens.org to generate an OOB token.

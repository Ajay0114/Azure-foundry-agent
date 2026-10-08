# HomeDelivery_Script_HandleScanResult  (script)

## Config
```json
{
  "name": "HomeDelivery_Script_HandleScanResult",
  "type": "script"
}
```

## script
```
context.uploadBlocked   = false;
context.uploadErrored   = false;
context.uploadBlockType = '';
context.zd_tokens       = [];

var nodeData = context.HomeDelivery_Service_ScanUpload;
var response = nodeData && nodeData.response;
var body     = response && response.body;

if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch (e) { body = {}; }
}
if (!body) body = {};

var code = parseInt(response && response.statusCode, 10);

if (code === 200) {
    context.zd_tokens = Array.isArray(body.tokens) ? body.tokens : [];
    // Store in session so PrepareZendeskData can read it
    context.session.BotUserSession.zd_tokens_combined = context.zd_tokens;

} else if (code === 422) {
    context.uploadBlocked = true;
    context.entities.HomeDelivery_Entity_Upload = null;

    if (body.blocked && body.blocked.length > 0) {
        var reason = body.blocked[0].reason || '';
        context.uploadBlockType = (reason.indexOf('File type') === 0)
            ? 'filetype' : 'malware';
    } else {
        context.uploadBlockType = 'malware';
    }

} else {
    context.uploadErrored = true;
    context.entities.HomeDelivery_Entity_Upload = null;
}

koreDebugger.log("Upload blocked: " + context.uploadBlocked);
koreDebugger.log("Upload errored: " + context.uploadErrored);
koreDebugger.log("Tokens: " + JSON.stringify(context.zd_tokens));
```

# HomeDelivery_Script_PrepareAzureData  (script)

## Config
```json
{
  "name": "HomeDelivery_Script_PrepareAzureData",
  "type": "script"
}
```

## script
```
// Reset flags on every fresh attempt
context.uploadBlocked   = false;
context.uploadErrored   = false;
context.uploadBlockType = '';
context.zd_tokens       = [];

var raw   = context.entities.HomeDelivery_Entity_Upload;
var files = [];

if (Array.isArray(raw) && raw.length > 0) {
    for (var i = 0; i < raw.length; i++) {
        var f = raw[i];
        if (!f) continue;
        var url  = f.fileUrl || (f.url && f.url.fileUrl);
        var name = f.fileName || ("attachment_" + (i + 1));
        if (url && name) files.push({ fileUrl: url, fileName: name });
    }
} else if (typeof raw === "string") {
    files = []; // skip or any text
}

// Debug log matching existing pattern
koreDebugger.log("X-Session-ID: " + context.session.BotUserSession.conversationSessionId);
koreDebugger.log("X-Customer-Email: " + context.session.BotUserSession.customerEmail);

context.azurePayloadString = JSON.stringify({ files: files });
context.skip_zd_upload     = (files.length === 0);

if (context.skip_zd_upload) {
    context.zd_tokens = [];
    context.session.BotUserSession.zd_tokens_combined = [];
}
```

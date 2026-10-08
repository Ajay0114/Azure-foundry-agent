# PC_HomeDelivery_Script_SavingAgentData  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_SavingAgentData",
  "type": "script"
}
```

## script
```
try {
    context.session = context.session || {};
    context.entities = context.entities || {};
    var s = context.session.BotUserSession = context.session.BotUserSession || {};

    if (s.exitReason === "exit_requested") {
        context.exitReason = "exit_requested";
        s.exitReason = null;
        s._returnDetailsInitialized = false;   // fresh start if user retries
        koreDebugger.log("SCRIPT | Routing to Cancel_Mid_Workflow");
    } else {
        context.exitReason = null;
        s.exitReason = null;

        var products = Array.isArray(s.products) ? s.products : [];

        // ── LAST LINE OF DEFENSE: drop slots with no product name ──
        var beforeFilter = products.length;
        products = products.filter(function(p) {
            return p && p.product_name && String(p.product_name).trim() !== "" &&
                   p.product_name !== "UNKNOWN";
        });
        if (products.length !== beforeFilter) {
            s.productDataAnomaly = true;
            koreDebugger.log("SCRIPT | WARN: dropped " + (beforeFilter - products.length) +
                             " nameless slot(s) before ticket build");
        }
        s.products = products;

        koreDebugger.log("SCRIPT | Total Products Collected: " + products.length);

        // ── CONDITION → INTEGER ENUM ──
        // 1 = used/damaged, 2 = new/unopened/wrong product, 0 = unknown
        var conditionMap = {
            "new": 2, "unopened": 2, "sealed": 2, "unused": 2, "wrong product": 2,
            "used": 1, "opened": 1, "damaged": 1,
            "unknown": 0
        };

        // ── [A5/C5] EXIT-PATH + COMPLETENESS GUARD ──
        // Normal exits are labeled by the agent node's post-processor
        // (completed / thats_all / user_cancelled). An UNLABELED arrival here
        // means the platform force-exited the agent node (Ghost-Referee) —
        // treat the data with maximum suspicion.
        var exitPath = s.agentNodeExitPath || "platform_fallback";
        s.agentNodeExitPath = null; // consume
        koreDebugger.log("SCRIPT | Agent node exit path: " + exitPath);

        function isComplete(p) {
            if (!p.product_name || p.product_name === "UNKNOWN") return false;
            if (!(parseInt(p.quantity) > 0)) return false;
            if (!p.condition || conditionMap[String(p.condition).toLowerCase().trim()] === undefined) return false;
            if (p.condition === "wrong product" &&
                (!p.expected_product_name || p.expected_product_name === "UNKNOWN")) return false;
            return true;
        }

        var completeProducts = products.filter(isComplete);
        var incompleteCount = products.length - completeProducts.length;

        // ═══ BUSINESS RULING ═══
        // Ticket is built from COMPLETE products only; incomplete ones are
        // excluded and flagged, never zero-filled.
        var productsToReturnArray = [];
        for (var j = 0; j < completeProducts.length; j++) {
            var p = completeProducts[j];
            productsToReturnArray.push({
                "productName": String(p.product_name).trim(),
                "quantity": parseInt(p.quantity),
                "productCondition": conditionMap[String(p.condition).toLowerCase().trim()],
                "expectedProductName": (p.expected_product_name || "").toString().trim(),
                "condition": String(p.condition).toLowerCase().trim()
            });
        }


        // ── [D12 Split-Truth] SUMMARY — built from the SAME guarded list used
        // for the ticket payload. Previously the summary was built earlier and
        // from the raw slots, so the customer email listed products (with
        // "Condition: N/A") that the completeness guard had excluded from the
        // ticket. Email and payload now always agree.
        var summary = "";
        if (productsToReturnArray.length > 0) {
            for (var si = 0; si < productsToReturnArray.length; si++) {
                var item = productsToReturnArray[si];
                summary += "• Product " + (si + 1) + ": " + item.productName +
                           " | Qty: " + item.quantity +
                           " | Condition: " + item.condition;
                if (item.condition === "wrong product" && item.expectedProductName) {
                    summary += " | Expected: " + item.expectedProductName;
                }
                summary += "\n";
            }
        } else {
            summary = "No products captured.";
        }
        if (incompleteCount > 0) {
            summary += "(" + incompleteCount + " item(s) were left incomplete and are not listed above.)\n";
        }
        s.all_products_summary = summary;
        koreDebugger.log("SCRIPT | Summary: " + summary);

        // ── [D8] COUNT RECONCILIATION — record, never reshape.
        var expectedCount = parseInt(s.ProductCount) || 0;
        var collectedUnits = 0;
        for (var qi = 0; qi < productsToReturnArray.length; qi++) {
            collectedUnits += parseInt(productsToReturnArray[qi].quantity) || 0;
        }
        s.collectedUnits = collectedUnits;
        s.countMismatch = (expectedCount > 0 && collectedUnits !== expectedCount);
        if (s.countMismatch) {
            koreDebugger.log("SCRIPT | WARN count mismatch — customer stated " + expectedCount +
                             " item(s), collected " + collectedUnits + " — flagged for review");
        }

        s.productsToReturn = productsToReturnArray;
        s.productsToReturnJSON = JSON.stringify(productsToReturnArray);
        s.ticket = s.ticket || {};
        s.ticket.productsToReturn = productsToReturnArray;
        s.ticket.productCount = productsToReturnArray.length;

        // Routing signals for connection rules (same pattern as context.exitReason):
        s.collectionOutcome =
            (productsToReturnArray.length === 0) ? "nothing_submittable" :
            (incompleteCount > 0 || s.countMismatch || exitPath === "platform_fallback") ? "partial_review" :
            "clean";
        context.collectionOutcome = s.collectionOutcome;

        s.agentNodeStarted = false;

        // Allow a fresh collection if the flow re-enters this node later
        s._returnDetailsInitialized = false;

        koreDebugger.log("SCRIPT | Final productsToReturn: " + s.productsToReturnJSON);
        if (s.collectionOutcome === "clean") {
            koreDebugger.log("SCRIPT | ✓ PRODUCTS READY FOR TICKET SUBMISSION" +
                             (s.partialReturn ? " (PARTIAL: user ended early)" : "") +
                             (s.productDataAnomaly ? " (ANOMALY: nameless slots dropped)" : ""));
        } else {
            koreDebugger.log("SCRIPT | ⚠ NOT CLEAN — outcome: " + s.collectionOutcome +
                             " | exitPath: " + exitPath +
                             " | incomplete slots excluded: " + incompleteCount +
                             " | countMismatch: " + s.countMismatch);
        }
    }

} catch (e) {
    koreDebugger.log("SCRIPT | EXCEPTION: " + e.message);
}

```

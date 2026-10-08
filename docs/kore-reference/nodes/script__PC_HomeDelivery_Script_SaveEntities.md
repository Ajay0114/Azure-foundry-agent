# PC_HomeDelivery_Script_SaveEntities  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_SaveEntities",
  "type": "script"
}
```

## script
```
try {
    var raw = context.GenerativeAINode &&
              context.GenerativeAINode.PC_HomeDelivery_PromptNode &&
              context.GenerativeAINode.PC_HomeDelivery_PromptNode.text;

    if (raw) {
        var clean = String(raw).replace(/```json|```/g, "").trim();

        var parsed = null;
        try {
            parsed = JSON.parse(clean);
        } catch (eParse) {
            koreDebugger.log("EXTRACT | JSON Parse Error: " + eParse.message);
        }

        if (parsed) {
            context.entities = context.entities || {};
            context.session = context.session || {};
            var s = context.session.BotUserSession = context.session.BotUserSession || {};
            s.piiEntities = s.piiEntities || {};   // guard against crash

            function isNonEmpty(v) {
                return v !== undefined && v !== null && String(v).trim() !== "" &&
                       v !== "null" && v !== "UNKNOWN";
            }

            // ---- CabinNumber (single or comma-joined multiple, one variable) ----
            if (isNonEmpty(parsed.cabin_number)) {
                var cabinRaw = String(parsed.cabin_number).trim();
                var parts = cabinRaw.split(/\s*[,&]\s*|\s+and\s+/i).filter(Boolean);
                var validCabins = [];
                for (var ci = 0; ci < parts.length; ci++) {
                    var cn = parts[ci].trim().toUpperCase();
                    if (/^[A-Z]{0,3}\d{1,6}[A-Z]{0,2}$/.test(cn) && cn.length <= 8) {
                        validCabins.push(cn);
                    } else {
                        koreDebugger.log("EXTRACT | Rejected cabin segment: " + cn);
                    }
                }
                if (validCabins.length > 0) {
                    var cabinOut = validCabins.join(",");
                    context.entities.CabinNumber = cabinOut;
                    s.CabinNumber = cabinOut;
                    s.resolvedCabinNumber = cabinOut;
                } else {
                    koreDebugger.log("EXTRACT | No valid cabin segments in: " + cabinRaw);
                }
            }

            // ---- PurchasedDate (raw, but must contain a digit and a
            //      plausible date shape; agent node does real validation) ----
            if (isNonEmpty(parsed.purchase_date_raw)) {
                var pd = String(parsed.purchase_date_raw).trim();
                if (/\d/.test(pd) && pd.length >= 6 && pd.length <= 30) {
                    context.entities.PurchasedDate = pd;
                    s.PurchasedDate = pd;
                } else {
                    koreDebugger.log("EXTRACT | Rejected date: " + pd);
                }
            }

            // ---- Country ----
            if (isNonEmpty(parsed.country)) {
                var country = String(parsed.country).trim();
                if (country.length >= 2 && /^[a-zA-Z\s\-'.]+$/.test(country)) {
                    context.entities.Country = country;
                    s.Country = country;
                    s.resolvedCountry = country;
                } else {
                    koreDebugger.log("EXTRACT | Rejected country: " + country);
                }
            }

            // ---- PhoneNumber (loose shape check; entity node re-validates) ----
            if (isNonEmpty(parsed.phone_number)) {
                var phone = String(parsed.phone_number).trim();
                if (/[\d]{6,}/.test(phone.replace(/[\s\-().+]/g, ""))) {
                    s.piiEntities.phoneNumber = phone;
                }
            }

            // ---- ProductCount (positive integer only — NEVER default) ----
            if (isNonEmpty(parsed.product_count)) {
                var pc = parseInt(parsed.product_count, 10);
                if (!isNaN(pc) && pc >= 1 && pc <= 999) {
                    context.entities.ProductCount = pc;
                    s.ProductCount = pc;
                    s.resolvedProductCount = String(pc);
                } else {
                    koreDebugger.log("EXTRACT | Rejected product_count: " + parsed.product_count);
                }
            }

            // ---- Products array (validate each slot's fields) ----
            if (Array.isArray(parsed.products) && parsed.products.length > 0) {
                var cleanProducts = [];
                for (var i = 0; i < parsed.products.length; i++) {
                    var p = parsed.products[i] || {};
                    var slot = {
                        product_name: null,
                        quantity: null,
                        condition: null,
                        expected_product_name: null
                    };
                    if (isNonEmpty(p.product_name) && !/^\d+$/.test(String(p.product_name).trim())) {
                        slot.product_name = String(p.product_name).trim();
                    }
                    if (isNonEmpty(p.quantity)) {
                        var q = parseInt(p.quantity, 10);
                        if (!isNaN(q) && q >= 1 && q <= 999) slot.quantity = String(q);
                    }
                    if (isNonEmpty(p.condition)) {
                        var c = String(p.condition).toLowerCase().trim();
                        if (["new","used","damaged","wrong product"].indexOf(c) !== -1) slot.condition = c;
                    }
                    if (isNonEmpty(p.expected_product_name)) {
                        slot.expected_product_name = String(p.expected_product_name).trim();
                    }
                    // keep the slot only if it carries at least one real field
                    if (slot.product_name || slot.quantity || slot.condition) {
                        cleanProducts.push(slot);
                    }
                }
                if (cleanProducts.length > 0) {
                    s.products = cleanProducts;
                }
            }

            // ---- UNKNOWN indicated fields ----
            var unknowns = parsed.unknown_indicated_fields || [];
            if (unknowns.indexOf("cabin_number") !== -1)      s.CabinNumberUnknown = true;
            if (unknowns.indexOf("purchase_date_raw") !== -1) s.PurchasedDateUnknown = true;
            if (unknowns.indexOf("country") !== -1)           s.CountryUnknown = true;
            if (unknowns.indexOf("phone_number") !== -1)      s.PhoneNumberUnknown = true;
            if (unknowns.indexOf("product_count") !== -1)     s.ProductCountUnknown = true;

            s.extractionStatus = parsed.extractionSuccessful || "processed";

            koreDebugger.log("EXTRACT | Mapped: " + JSON.stringify({
                CabinNumber:   context.entities.CabinNumber,
                PurchasedDate: context.entities.PurchasedDate,
                Country:       context.entities.Country,
                PhoneNumber:   s.piiEntities.phoneNumber,
                ProductCount:  context.entities.ProductCount,
                ProductsLen:   (s.products || []).length,
                Unknowns:      unknowns
            }));
        }
    } else {
        koreDebugger.log("EXTRACT | No prompt node output");
    }

} catch (e) {
    koreDebugger.log("EXTRACT | Script Error: " + e.message);
}
```

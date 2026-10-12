/* Marina chat widget. No dependencies, no debug code. Embed with:
 *
 *   <link rel="stylesheet" href="https://YOUR-HOST/widget.css">
 *   <script src="https://YOUR-HOST/widget.js"></script>
 *   <script>MarinaChat.init({ api: "https://YOUR-HOST" });</script>
 *
 * Options (all optional):
 *   api         base address of the server that offers POST /api/chat (default: the page's own origin)
 *   name        header name                          default "MARINA"
 *   subtitle    line under the name                  default "Your personal assistant"
 *   avatar      image URL for the round avatar       default: the first letter of the name
 *   color       brand colour (header, launcher, chips, customer bubbles)
 *   greeting    first bot message                    default "Hi, I'm Marina. How can I help you today?"
 *   buttons     chips under the greeting             default ["Return a product"]
 *   teasers     bubbles above the closed launcher    default []
 *   container   an element (or selector): show the chat inside it, always open, with no launcher
 *   onReply     function(info) called after each bot reply with {session, previous}
 *   onReset     function() called when the customer starts over
 */
(function () {
  "use strict";
  var ICON = {
    chat: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 4h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-5 4v-4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/></svg>',
    back: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>',
    refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"/></svg>',
    close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    menu: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    clip: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11l-8.5 8.5a5 5 0 0 1-7-7L14 4a3.5 3.5 0 0 1 5 5l-8.5 8.5a2 2 0 0 1-3-3L15 7"/></svg>',
    smile: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M8 14a4.5 4.5 0 0 0 8 0M9 9.5h.01M15 9.5h.01"/></svg>',
    mic: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>',
    send: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 20l18-8L3 4v6l11 2-11 2z"/></svg>'
  };
  var EMOJI = ["😀", "😊", "😍", "👍", "🙏", "😢", "😡", "🎉", "❤️", "👋", "✅", "❓"];
  var LINK = /(https?:\/\/[^\s<>"']+[^\s<>"'.,;:!?)])/g;

  function el(tag, cls, html) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (html) node.innerHTML = html;
    return node;
  }
  function clock() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }).toLowerCase() + ", Today";
  }
  function safe(fn) { try { return fn(); } catch (e) { return null; } }

  /* Bot text is shown as text; only plain http(s) links become clickable. Nothing from the bot is ever inserted as HTML. */
  function fill(bubble, text) {
    String(text).split(LINK).forEach(function (part, i) {
      if (i % 2) {
        var a = document.createElement("a");
        a.href = part; a.textContent = part; a.target = "_blank"; a.rel = "noopener noreferrer";
        bubble.appendChild(a);
      } else if (part) {
        bubble.appendChild(document.createTextNode(part));
      }
    });
  }

  function init(opts) {
    opts = opts || {};
    var api = (opts.api || "").replace(/\/$/, "");
    var name = opts.name || "MARINA";
    var greeting = opts.greeting || "Hi, I'm Marina. How can I help you today?";
    var buttons = opts.buttons || ["Return a product"];
    var holder = opts.container ? (typeof opts.container === "string" ? document.querySelector(opts.container) : opts.container) : null;
    var key = "marina-chat:" + (opts.storageKey || location.host);
    var state = { session: null, previous: null, busy: false, files: [] };

    var root = el("div", "mw" + (holder ? " mw-inline" : ""));
    if (opts.color) root.style.setProperty("--mw-brand", opts.color), root.style.setProperty("--mw-user", opts.color);
    var launcher, teasers;
    var panel = el("div", "mw-panel");
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", name + " chat");
    var avatar = el("div", "mw-avatar");
    if (opts.avatar) { var img = el("img"); img.src = opts.avatar; img.alt = ""; avatar.appendChild(img); } else { avatar.textContent = name.charAt(0).toUpperCase(); }
    var titles = el("div", "mw-titles", '<div class="mw-name"></div><div class="mw-sub"></div>');
    titles.firstChild.textContent = name;
    titles.lastChild.textContent = opts.subtitle || "Your personal assistant";
    var head = el("div", "mw-head");
    var btnBack = el("button", "", ICON.back), btnReset = el("button", "", ICON.refresh), btnClose = el("button", "", ICON.close);
    btnBack.title = "Minimise"; btnBack.setAttribute("aria-label", "Minimise chat");
    btnReset.title = "Start over"; btnReset.setAttribute("aria-label", "Start a new conversation");
    btnClose.title = "Close"; btnClose.setAttribute("aria-label", "Close chat");
    if (!holder) head.appendChild(btnBack);
    head.appendChild(avatar); head.appendChild(titles); head.appendChild(btnReset);
    if (!holder) head.appendChild(btnClose);
    var log = el("div", "mw-log");
    log.setAttribute("aria-live", "polite");
    var foot = el("div", "mw-foot");
    var btnMenu = el("button", "", ICON.menu), btnClip = el("button", "", ICON.clip), btnEmoji = el("button", "", ICON.smile);
    var btnMic = el("button", "", ICON.mic), btnSend = el("button", "mw-send", ICON.send);
    btnMenu.title = "Menu"; btnClip.title = "Attach a file by link"; btnEmoji.title = "Emoji"; btnMic.title = "Voice (not available)"; btnSend.title = "Send";
    btnMenu.setAttribute("aria-label", "Menu"); btnClip.setAttribute("aria-label", "Attach a file by link"); btnEmoji.setAttribute("aria-label", "Emoji");
    btnMic.setAttribute("aria-label", "Voice input not available"); btnSend.setAttribute("aria-label", "Send");
    var input = el("input", "mw-input");
    input.type = "text"; input.placeholder = "Type a message"; input.autocomplete = "off"; input.maxLength = 2000;
    input.setAttribute("aria-label", "Type a message");
    var menu = el("div", "mw-menu"), emoji = el("div", "mw-emoji");
    menu.hidden = emoji.hidden = true;
    [["Start over", reset], ["Attach a file link", attach]].forEach(function (item) {
      var b = el("button"); b.textContent = item[0]; b.onclick = function () { menu.hidden = true; item[1](); }; menu.appendChild(b);
    });
    EMOJI.forEach(function (ch) {
      var b = el("button"); b.textContent = ch; b.onclick = function () { input.value += ch; emoji.hidden = true; input.focus(); }; emoji.appendChild(b);
    });
    [btnMenu, btnClip, input, btnEmoji, btnMic, btnSend, menu, emoji].forEach(function (n) { foot.appendChild(n); });
    panel.appendChild(head); panel.appendChild(log); panel.appendChild(foot);
    root.appendChild(panel);

    if (holder) {
      holder.appendChild(root);
    } else {
      panel.hidden = true;
      launcher = el("button", "mw-launcher", ICON.chat);
      launcher.setAttribute("aria-label", "Open chat with " + name);
      teasers = el("div", "mw-teasers");
      (opts.teasers || []).forEach(function (text) {
        var t = el("div", "mw-teaser"); t.textContent = text; t.onclick = open; teasers.appendChild(t);
      });
      root.appendChild(teasers); root.appendChild(launcher);
      document.body.appendChild(root);
      launcher.onclick = function () { panel.hidden ? open() : close(); };
      btnBack.onclick = btnClose.onclick = close;
    }

    function open() { panel.hidden = false; if (teasers) teasers.hidden = true; if (launcher) launcher.hidden = true; input.focus(); scroll(); }
    function close() { panel.hidden = true; if (launcher) launcher.hidden = false; }
    function scroll() { log.scrollTop = log.scrollHeight; }
    function save() { safe(function () { sessionStorage.setItem(key, JSON.stringify({ s: state.session, p: state.previous, h: history })); }); }

    var history = [];                       // [{who, text}] so a page reload keeps the conversation on screen
    function bubble(who, text, cls) {
      var wrap = el("div", "mw-msg " + who), label = el("div", "mw-who"), b = el("div", "mw-bubble" + (cls ? " " + cls : ""));
      label.textContent = who === "bot" ? name.charAt(0) + name.slice(1).toLowerCase() + " " + clock() : "You " + clock();
      fill(b, text);
      wrap.appendChild(label); wrap.appendChild(b); log.appendChild(wrap); scroll();
      return wrap;
    }
    function clearChips() { Array.prototype.slice.call(log.querySelectorAll(".mw-chips")).forEach(function (n) { n.remove(); }); }
    function chips(labels) {
      clearChips();
      if (!labels || !labels.length) return;
      var row = el("div", "mw-chips");
      labels.forEach(function (label) {
        var b = el("button", "mw-chip"); b.textContent = label; b.onclick = function () { send(label); }; row.appendChild(b);
      });
      log.appendChild(row); scroll();
    }
    function typing(on) {
      var t = log.querySelector(".mw-typing-row");
      if (on && !t) { t = el("div", "mw-msg bot mw-typing-row", '<div class="mw-bubble mw-typing"><i></i><i></i><i></i></div>'); log.appendChild(t); scroll(); }
      if (!on && t) t.remove();
    }
    function busy(on) { state.busy = on; btnSend.disabled = on; typing(on); }

    function send(text) {
      text = (text == null ? input.value : text).trim();
      if (!text && !state.files.length || state.busy) return;
      input.value = ""; clearChips();
      bubble("user", text || "(file)"); history.push({ who: "user", text: text || "(file)" });
      busy(true);
      var body = JSON.stringify({ text: text, files: state.files, previous: state.previous, session: state.session });
      state.files = [];
      fetch(api + "/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: body })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          busy(false);
          if (data.error) { bubble("bot", data.error, "err"); return; }
          state.previous = data.previous || state.previous;
          state.session = data.session || state.session;
          String(data.reply || "").split(/\n{2,}/).forEach(function (part) {
            if (part.trim()) { bubble("bot", part.trim()); history.push({ who: "bot", text: part.trim() }); }
          });
          chips(data.suggestions);
          save();
          if (opts.onReply) safe(function () { opts.onReply({ session: state.session, previous: state.previous }); });
        })
        .catch(function () { busy(false); bubble("bot", "Sorry, I could not reach the assistant. Please try again.", "err"); });
    }

    function attach() {
      var link = window.prompt("Paste the link (https://…) to the photo or document to attach:");
      if (link && /^https:\/\//i.test(link.trim())) { state.files.push(link.trim()); bubble("user", "📎 " + link.trim()); }
      else if (link) { bubble("bot", "Only https:// links can be attached.", "err"); }
    }

    function start(keepHistory) {
      log.innerHTML = '<div class="mw-end">End of chat history</div>';
      if (keepHistory) {
        history.forEach(function (m) { bubble(m.who, m.text); });
        return;
      }
      history = [{ who: "bot", text: greeting }];
      bubble("bot", greeting);
      chips(buttons);
    }
    function reset() {
      state.session = state.previous = null; state.files = [];
      safe(function () { sessionStorage.removeItem(key); });
      start(false);
      if (opts.onReset) safe(opts.onReset);
    }

    btnReset.onclick = reset;
    btnSend.onclick = function () { send(); };
    input.onkeydown = function (e) { if (e.key === "Enter") { e.preventDefault(); send(); } };
    btnMenu.onclick = function () { menu.hidden = !menu.hidden; emoji.hidden = true; };
    btnEmoji.onclick = function () { emoji.hidden = !emoji.hidden; menu.hidden = true; };
    btnClip.onclick = attach;
    btnMic.onclick = function () { bubble("bot", "Voice input is not available yet. Please type your message."); };

    var saved = safe(function () { return JSON.parse(sessionStorage.getItem(key) || "null"); });
    if (saved && saved.h && saved.h.length) { state.session = saved.s; state.previous = saved.p; history = saved.h; start(true);
      if (opts.onReply) safe(function () { opts.onReply({ session: state.session, previous: state.previous }); }); }
    else { start(false); }
    if (holder) input.focus();
    return { open: open, close: close, reset: reset };
  }

  window.MarinaChat = { init: init };
})();

// Tennis Daily location bot — Supabase Edge Function (webhook).
// A visitor taps "Send to Telegram" on tennisdaily.uz → t.me/<bot>?start=court_<id>_<lang>
// → the bot replies with the court name and a native Telegram location (sendLocation).
//
// Secret (Supabase → Edge Functions → Secrets), never in Git:
//   TG_LOCATION_BOT_TOKEN  bot token from @BotFather
// The webhook secret is derived from the token (SHA-256), so nothing else has to be stored;
// Telegram sends it back in a header on every update and other callers get 403.
// Optional: COURTS_URL (default: tennisdaily.uz/courts.json, then the same file on GitHub).
//
// One-time setup after the token is set: open <function URL>?setup=1
// (idempotent: it only points this bot's webhook at this function).
// Health check (no secrets): <function URL>?health=1

type Lang = "ru" | "uz" | "en";
type Court = { id: string; name: Record<Lang, string>; lat: number; lon: number };

const TOKEN = Deno.env.get("TG_LOCATION_BOT_TOKEN") ?? "";
const SECRET = TOKEN
  ? Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode("tennisdaily-location:" + TOKEN))))
    .map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 48)
  : "";
const COURTS_URLS = Deno.env.get("COURTS_URL")
  ? [Deno.env.get("COURTS_URL")!]
  : ["https://tennisdaily.uz/courts.json", "https://raw.githubusercontent.com/dandesdet/tennisdaily/main/courts.json"];
const SITE = "https://tennisdaily.uz/#courts";
const API = Deno.env.get("TG_API_BASE") ?? "https://api.telegram.org"; // overridable for local tests only
const ID_RE = /^[a-z0-9-]{1,40}$/;
const START_RE = /^court_([a-z0-9-]{1,40})(?:_(ru|uz|en))?$/;

const T: Record<string, Record<Lang, string>> = {
  hello: {
    ru: "Здравствуйте! Откройте корт на tennisdaily.uz и нажмите «Отправить в Telegram» — я пришлю его геолокацию.",
    uz: "Assalomu alaykum! tennisdaily.uz saytida kortni oching va «Telegramga yuborish» tugmasini bosing — joylashuvini yuboraman.",
    en: "Hi! Open a court on tennisdaily.uz and tap “Send to Telegram” — I’ll send you its location.",
  },
  notFound: {
    ru: "Не нашёл этот корт. Откройте его на сайте ещё раз.",
    uz: "Bu kort topilmadi. Uni saytda qaytadan oching.",
    en: "I couldn’t find this court. Please open it on the site again.",
  },
  down: {
    ru: "Не получилось загрузить список кортов. Попробуйте через минуту.",
    uz: "Kortlar ro‘yxatini yuklab bo‘lmadi. Bir daqiqadan keyin urinib ko‘ring.",
    en: "Couldn’t load the court list. Please try again in a minute.",
  },
  site: { ru: "Корты на сайте", uz: "Saytdagi kortlar", en: "Courts on the site" },
  route: { ru: "Маршрут в Яндекс Картах", uz: "Yandex Xaritada yo‘nalish", en: "Route in Yandex Maps" },
  again: { ru: "Прислать ещё раз", uz: "Yana yuborish", en: "Send again" },
};

// ---- courts.json with a 10-minute cache; a stale copy is kept if the site is unreachable
let cache: { at: number; courts: Map<string, Court> } | null = null;
async function courts(): Promise<Map<string, Court> | null> {
  if (cache && Date.now() - cache.at < 10 * 60e3) return cache.courts;
  try {
    let data: any = null;
    for (const u of COURTS_URLS) {
      try {
        const r = await fetch(u, { headers: { "cache-control": "no-cache" } });
        if (r.ok) { data = await r.json(); break; }
        console.error(`courts.json HTTP ${r.status} at ${u}`);
      } catch (e) { console.error(`courts.json unreachable at ${u}:`, (e as Error).message); }
    }
    if (!data) throw new Error("no courts source reachable");
    const map = new Map<string, Court>();
    for (const c of data.courts ?? []) {
      const ok = typeof c.id === "string" && ID_RE.test(c.id) &&
        Number.isFinite(c.lat) && Number.isFinite(c.lon) &&
        Math.abs(c.lat) <= 90 && Math.abs(c.lon) <= 180 && !(c.lat === 0 && c.lon === 0);
      if (ok) map.set(c.id, c);
    }
    cache = { at: Date.now(), courts: map };
    return map;
  } catch (e) {
    console.error("courts load failed:", (e as Error).message);
    return cache?.courts ?? null;
  }
}

// ---- Telegram API with retries for network errors, 429 and 5xx
async function tg(method: string, body: unknown): Promise<any> {
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const r = await fetch(`${API}/bot${TOKEN}/${method}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
      const j = await r.json().catch(() => ({}));
      if (j.ok) return j.result;
      const retryAfter = j.parameters?.retry_after;
      if ((r.status === 429 || r.status >= 500) && attempt < 3) {
        await new Promise((res) => setTimeout(res, Math.min((retryAfter ?? attempt) * 1000, 3000)));
        continue;
      }
      console.error(`${method} failed: ${r.status} ${j.description ?? ""}`);
      return null;
    } catch (e) {
      console.error(`${method} network error (attempt ${attempt}):`, (e as Error).message);
      if (attempt < 3) await new Promise((res) => setTimeout(res, attempt * 700));
    }
  }
  return null;
}

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const pickLang = (fromParam?: string, code?: string): Lang =>
  (fromParam as Lang) || (code?.startsWith("ru") ? "ru" : code?.startsWith("uz") ? "uz" : code ? "en" : "uz");
const siteButton = (lang: Lang) => ({ inline_keyboard: [[{ text: T.site[lang], url: SITE }]] });

async function sendCourt(chat: number, id: string, lang: Lang) {
  if (!ID_RE.test(id)) return tg("sendMessage", { chat_id: chat, text: T.notFound[lang], reply_markup: siteButton(lang) });
  const list = await courts();
  if (!list) return tg("sendMessage", { chat_id: chat, text: T.down[lang] });
  const c = list.get(id);
  if (!c) return tg("sendMessage", { chat_id: chat, text: T.notFound[lang], reply_markup: siteButton(lang) });
  const name = c.name[lang] || c.name.ru;
  await tg("sendMessage", { chat_id: chat, text: `🎾 <b>${esc(name)}</b>`, parse_mode: "HTML" });
  await tg("sendLocation", {
    chat_id: chat,
    latitude: c.lat,
    longitude: c.lon,
    reply_markup: {
      inline_keyboard: [
        [{ text: T.route[lang], url: `https://yandex.uz/maps/?rtext=~${c.lat},${c.lon}&rtt=auto` }],
        [{ text: T.again[lang], callback_data: `loc:${c.id}:${lang}` }],
      ],
    },
  });
}

async function handleUpdate(u: any) {
  if (u.callback_query) {
    const q = u.callback_query;
    await tg("answerCallbackQuery", { callback_query_id: q.id });
    const m = /^loc:([a-z0-9-]{1,40}):(ru|uz|en)$/.exec(q.data ?? "");
    const chat = q.message?.chat?.id;
    if (m && chat) await sendCourt(chat, m[1], m[2] as Lang);
    return;
  }
  const msg = u.message;
  if (!msg?.chat?.id || msg.chat.type !== "private") return;
  const text: string = msg.text ?? "";
  const code = msg.from?.language_code;
  const start = /^\/start(?:@\w+)?(?:\s+(\S+))?/.exec(text);
  const m = start?.[1] ? START_RE.exec(start[1]) : null;
  if (m) return sendCourt(msg.chat.id, m[1], pickLang(m[2], code));
  const lang = pickLang(undefined, code);
  return tg("sendMessage", { chat_id: msg.chat.id, text: T.hello[lang], reply_markup: siteButton(lang) });
}

Deno.serve(async (req) => {
  const url = new URL(req.url);
  if (req.method === "GET") {
    if (url.searchParams.has("health")) {
      const list = await courts();
      return Response.json({ ok: true, token: Boolean(TOKEN), secret: Boolean(SECRET), courts: list?.size ?? 0 });
    }
    if (url.searchParams.has("setup") && TOKEN) {
      const hook = `https://${url.host}${url.pathname}`;
      const set = await tg("setWebhook", {
        url: hook, secret_token: SECRET, allowed_updates: ["message", "callback_query"], drop_pending_updates: true,
      });
      const info = await tg("getWebhookInfo", {});
      const me = await tg("getMe", {});
      return Response.json({ setWebhook: set, bot: me?.username, webhook: { url: info?.url, pending: info?.pending_update_count, last_error: info?.last_error_message } });
    }
    return new Response("Not found", { status: 404 });
  }
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });
  if (!SECRET || req.headers.get("x-telegram-bot-api-secret-token") !== SECRET) return new Response("Forbidden", { status: 403 });
  if (!TOKEN) return new Response("Bot token is not configured", { status: 500 });
  try {
    await handleUpdate(await req.json());
  } catch (e) {
    console.error("update failed:", (e as Error).message);
  }
  return new Response("ok"); // always 200 so Telegram doesn't re-send the same update
});

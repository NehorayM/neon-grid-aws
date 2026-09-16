# Turning on accounts and cloud sync

The app works with no backend at all — progress saves to `localStorage` on whatever browser
you're using. Accounts are optional on top of that: sign in and the same progress follows you
between devices.

Everything below fits inside Supabase's free tier.

---

## 1. Create the project

1. Sign up at [supabase.com](https://supabase.com) and create a new project.
2. Pick a region near you and set a database password (that's the *database* password — you
   won't need it in the app).
3. Wait for provisioning to finish, ~2 minutes.

## 2. Create the table and its security rules

1. In the dashboard, open **SQL Editor → New query**.
2. Paste the whole of [`supabase_setup.sql`](supabase_setup.sql) and run it.
3. Check the output — it creates one `profiles` table, enables row-level security, and adds
   four policies.

The last two lines of that file are verification queries. Run them and confirm:

- `rowsecurity` is `true` for `profiles`
- four policies exist (select / insert / update / delete)

**This matters more than anything else on this page.** The key in step 3 is public. Row-level
security is the only thing stopping one player from reading another's row.

## 3. Point the app at it

1. In the dashboard: **Settings → API**.
2. Copy the **Project URL** and the **anon / public** key.
3. Open `index.html`, find the `SUPA` block near the top of the script, and fill it in:

```js
const SUPA={
  url:'https://YOUR-PROJECT.supabase.co',
  anonKey:'eyJhbGciOi...'      // the anon / public key
};
```

4. Commit and push. GitHub Pages redeploys in about a minute.

> **Only ever use the `anon` key here.** The `service_role` key on that same page bypasses
> row-level security entirely — pasting it into a public page would expose every user's data.
> The anon key is designed to ship in a browser; that's why it's called publishable.

## 4. Email confirmation (optional but recommended)

By default Supabase emails a confirmation link before a new account can sign in. To change it:
**Authentication → Providers → Email**, toggle *Confirm email*.

- **On** (default): more friction, but real email addresses and no throwaway signups.
- **Off**: instant signup, fine for a study tool you're sharing with a few people.

The free tier's built-in email sender is rate-limited to a handful of messages per hour. If
you expect more signups than that, attach your own SMTP under **Settings → Auth → SMTP**.

---

## How syncing behaves

- **Guests** never touch the network. Progress lives in `localStorage`, same as before.
- **Signing in** merges what's on the device with what's in the cloud, keeping the better of
  each: highest XP, coins and streaks; the union of seen questions, badges, bookmarks and the
  review queue; per-sector stats from whichever device answered more. Nothing is discarded,
  so numbers can jump upward on first sign-in.
- **During play**, saves are debounced and pushed about four seconds after the last change.
- **Signing out** pushes one final time, then leaves the local copy alone.
- **Offline or backend down**: the app says so, keeps playing on `localStorage`, and syncs on
  the next successful save. It never blocks the game on the network.

## What's stored

One row per user in `public.profiles`:

| Column | Contents |
|---|---|
| `id` | The Supabase auth user id (foreign key to `auth.users`) |
| `profile` | The game profile: XP, coins, seen questions, badges, per-sector stats, course records |
| `course` | An in-flight Subject Course, so a refresh mid-course can resume on another device |
| `updated_at` | Touched by a trigger on every write |

Passwords are **not** in this table and never pass through the app's own storage. Supabase Auth
owns them in `auth.users`, hashed with bcrypt, along with sessions and reset tokens.

## Free-tier limits worth knowing

- 500 MB database — a profile is a few KB, so that's thousands of users.
- 50,000 monthly active users.
- **A free project pauses after about a week with no requests.** You resume it with one click
  in the dashboard; nothing is lost. If the app is going to sit idle for stretches, that's the
  one thing that will surprise you.

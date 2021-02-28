# clan.l33t.xyz

NextJS-based frontend app for gaming clan pages hosted on <l33t.xyz>

# Architecture

- Live website: <https://clan.l33t.xyz> (Fallback: <http://clan-l33t-xyz.vercel.app>)
- Hosting is provided by Vercel.
- Airtable as the database
- Custom code for proxying/rendering 

# Local Development

To develop locally, perform the following steps:

1. `git clone`
1. `yarn install` and `yarn run dev`
1. Two options, one involving editing the hosts file, one not:
  1. Modify hosts file (i.e. `/etc/hosts`) and point `yourclan.clan.l33t.xyz` to `127.0.0.1`, then, in your browser, navigate to `http://<yourclan>.clan.l33t.xyz:3000`
  1. Alternately, without editing the hosts file, in your browser, navigate to `http://localhost:3000/<yourclan>`. However, with this method, not all routing may work correctly

# License

MIT License. See `LICENSE.md`

# Contributing

Contributions are welcome. Please fork and submit a pull request

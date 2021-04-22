# clan.l33t.xyz

Free, flexible, and robust gaming clan websites built on a convenient CMS powered by NextJS, Airtable, GitHub, and Vercel.

# Clans on `clan.l33t.xyz`

The list of gaming clan websites hosted on `clan.l33t.xyz` is growing. The first one is [Clan Amazon](https://amazon.clan.l33t.xyz), which is maintained by the creator of `l33t-xyz`.

# Host Your Clan Website on `clan.l33t.xyz`

Get a fully customizable clan website up and running in 10 minutes!

Instructions coming soon. For now, if you are interested, please shoot an email to <clan@l33t.xyz>, or in Aardwolf, send a tell to `Ruhamah`.

# Customization

While eventually, the site will be fully customizable, currently, the customizations are around hero (header) images, and color themes. The current color theme choices are: `default`, `dark-inferno`, `dark-forest`, `dark-steel-blue`, `dark-amethyst`, and `dark-bronze`.

# Architecture

- Live website: <https://clan.l33t.xyz> (Fallback: <http://clan-l33t-xyz.vercel.app>)
- Hosting is provided by [Vercel](https://vercel.com) (from the [l33t-xyz-bot mirror/fork](https://github.com/l33t-xyz-bot/clan.l33t.xyz))
- [Airtable](https://airtable.com) serves as the database, with content entered as [MDX](https://mdxjs.com), an extension of [Markdown](https://en.wikipedia.org/wiki/Markdown)
- Custom code for proxying/rendering from <https://l33t.xyz>

# Local Development

To develop locally, perform the following steps:

1. `git clone`
1. `yarn install` and `yarn run dev`
1. Two options, one involving editing the hosts file, one not:
  1. Modify hosts file (i.e. `/etc/hosts`) and point `yourclan.clan.l33t.xyz` to `127.0.0.1`, then, in your browser, navigate to `http://<yourclan>.clan.l33t.xyz:3000`
  1. Alternately, without editing the hosts file, in your browser, navigate to `http://localhost:3000/<yourclan>`. However, with this method, not all routing may work correctly

# Need more help?

Check out the [official wiki](https://github.com/l33t-xyz/clan.l33t.xyz/wiki) and the [FAQ](https://github.com/l33t-xyz/clan.l33t.xyz/wiki/FAQ)

# License

MIT License. See `LICENSE.md`

# Contributing

Contributions are welcome. Please fork and submit a pull request

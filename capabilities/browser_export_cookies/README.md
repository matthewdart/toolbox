# browser.export_cookies

## Description

Export browser cookies for a specific domain to a Netscape-format cookies.txt file. Uses yt-dlp's cookie extraction to read from Safari, Chrome, or Firefox cookie stores. The output file can be passed to `media.download_video` (via `cookies_path`) for authenticated downloads from login-gated sites.

## Non-goals

- Managing or modifying browser cookies
- Decrypting cookies from remote machines (must run locally)
- Supporting browsers other than those supported by yt-dlp
- Automatic cookie refresh or session management

## Deterministic behavior

Given the same browser, domain, and cookie store state, the exported cookies.txt is deterministic. The output file path is always the resolved absolute path of the `output` argument.

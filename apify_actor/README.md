# Parallax public SF Actor

Custom Python Actor for Parallax. It collects public numerical observations that actually initialize business prices and household wage references in new simulations. It runs with limited permissions. No Apify SDK, browser, proxy, or general-purpose scraper is required.

## Input

Run once for each category:

```json
{"category":"prices"}
```

```json
{"category":"wages"}
```

Only these categories are accepted. The sources are fixed in code. Caller-supplied URLs, executable scraping functions and arbitrary storage destinations are unsupported.

## Output and scope

The default dataset contains records with `item`, numeric `value`, `unit`, `kind`, `source_url` and UTC `observed_at`.

| Category | Source | Additional fields | Interpretation |
| --- | --- | --- | --- |
| prices | Cafe Seventy8 public menu | `variant`, `venue` | Posted drink-price options at one venue. Sizes and taxes are not inferred. |
| wages | SF official minimum-wage page | `effective_date` | General statutory minimum wage, not average earnings. |

Source changes can alter counts or cause parsing to fail. A successful historical collection had 29 menu-price options and one wage reference. These counts are evidence of that run, not a permanent output contract. The consumer records Actor/run/dataset IDs and applies the explicit eight-hour workday conversion; the Actor itself returns hourly USD.

## Collection behavior

The Actor checks source robots.txt, ignores script/style content, parses known patterns and fails rather than fabricating missing observations. Public requests do not receive the Apify token. Platform requests use the run token to read its own input and write its default dataset. Logs report only category/count.

The application's runner requests 128 MB, a 120-second timeout, no restart and no proxy. See [collection limits and provenance](https://github.com/shivanginarayan/CalHacks/blob/main/docs/APIFY.md) for usage, cache and deduplication behavior. The charge option is not an all-inclusive billing cap.

## Deploy and demonstrate

Configure the private root environment as described in [setup](https://github.com/shivanginarayan/CalHacks/blob/main/docs/APIFY.md), then run from repository root:

```powershell
.\.venv\Scripts\python.exe -m scripts.deploy_apify
```

This command creates or updates the configured Actor and starts a build. Use it for initial deployment or deliberate source updates, not each app launch. The app automatically loads saved observations and collects missing/stale inputs. Each new world freezes the complete sample and checksum; forks and resets preserve it. Financial identities, opening balances, employment relationships and behavior remain synthetic.

## Use in Parallax

The app loads saved public observations automatically, refreshes stale sources, and freezes inputs in each new simulated world. Bank balances, households, employment relationships and rescue outcomes are synthetic simulation state, not observations collected by this Actor.

Project source and setup: https://github.com/shivanginarayan/CalHacks

## Example record

This is an actual historical observation, not a promise about the next run:

```json
{"item":"HOUSE COFFEE","value":3.95,"unit":"usd_item","kind":"listed_menu_price_before_unspecified_tax_or_surcharges","source_url":"https://www.cafeseventy8.com/","observed_at":"2026-10-25T12:29:03.043599+00:00","variant":"listed option 1 (size unspecified)","venue":"Cafe Seventy8, 78 29th Street, San Francisco"}
```

## Cost and limitations

No rental or per-result fee is configured by the author. Standard Apify platform usage charges may apply. Use 128 MB and a 120-second timeout for this bounded collector. Source availability and page structure can change; missing observations fail explicitly. This is a narrow public reference collector, not a national economic forecast or personal credit dataset.

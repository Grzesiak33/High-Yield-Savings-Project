# High-Yield Savings Project — Mobile App Roadmap

Status: Streamlit web app is production baseline. Mobile target: React Native + Expo, Android/Google Play first, with iOS-compatible architecture.

## Goal
Keep the current Python/Streamlit app as the working web dashboard while making the repository ready for a future native mobile client. The native app should preserve the High-Yield Savings Project branding, approved savings hero artwork, savings calculations, dividend forecast, deposit projections, strategy view, and history.

## Recommended architecture
- `high_yield_savings_app.py` — current production Streamlit app.
- `data/` — current savings history/source data.
- `assets/` — shared brand and hero assets.
- `mobile/` — future Expo/React Native application.
- Mobile calculation logic should be implemented as testable TypeScript modules rather than depending on Streamlit.
- Keep financial assumptions/configuration centralized: current balance, 10% APY first $1,000, 0.10% excess tier, deposit cadence, and future second-bucket APY.

## Expo mobile build target
Use current Expo + React Native + TypeScript and EAS Build/Submit.

Suggested future files:
- `mobile/app.json` or `mobile/app.config.ts`
- `mobile/eas.json`
- `mobile/package.json`
- `mobile/tsconfig.json`
- `mobile/app/` Expo Router screens
- `mobile/src/finance/` calculation modules
- `mobile/src/components/` reusable dashboard cards/charts
- `mobile/assets/` mobile-ready app icon, splash/adaptive icon and approved hero image
- `mobile/__tests__/` projection/dividend tests

## Screens
1. Dashboard — balance, $1,000 progress, next deposit, projected $1K date.
2. Dividends — next monthly dividend estimate and accrual visualization.
3. Projections — paycheck-deposit scenario comparison.
4. Strategy — post-$1,000 savings routing / second savings bucket.
5. History — actual deposits/dividends and reported APY.

## Store readiness
Before a public Android launch:
- Choose a permanent Android package identifier (example only: `com.highyieldsavingsproject.app`).
- Create Expo/EAS project and production build profile.
- Generate a signed Android App Bundle (`.aab`) with EAS Build.
- Create and verify the appropriate Google developer account.
- Create the Play Console app/store listing.
- Prepare app icon, adaptive icon, splash assets, screenshots, description, support contact, privacy policy, and Data Safety disclosures.
- Configure Google Play service-account credentials for EAS Submit if automated submission is desired.
- Test through Play internal/closed testing before production rollout.

## Important policy checkpoint
Because this app concerns personal savings/financial information, check the then-current Google Play financial-services classification and developer-account requirements before creating the store account or submitting. Do not imply that the app is a bank, credit union, financial institution, or affiliated with ORSA unless authorized.

## Data/privacy design
The current project can remain a private personal savings tracker without bank credentials. A mobile version should initially store user-entered settings/history locally on-device unless a deliberate cloud-sync feature is added. Never commit bank account numbers, routing numbers, passwords, API secrets, Play service-account JSON, signing keys, or other credentials to GitHub.

## Definition of turnkey
The project is considered launch-ready when the `mobile/` app can be cloned, dependencies installed, tests run, an EAS production `.aab` built, the app installed/tested, required store metadata/privacy declarations completed, and the signed build submitted to the chosen Play testing/production track without rewriting the product.

## Power Log

A record of power usage with web and mobile interface.

## Design

### Database

A relational database with these tables.

| Table  | Use                     |
|--------|-------------------------|
| Site   | Description of the site or source being logged. |
| Usage  | Daily (or whatever) log of power, including user who made the entry.|
| Log    | A record of all changes to the Usage table. |

### Database Providers

Possible providers are:

- [Neon](https://neon.com)
  - Free tier: 0.5 GB storage, 190 compute hours/mo, 5 GB/mo egress
  - Paid tier: $19/month, 100 projects, 10 GB storage, 300 compute hours

- [Supabase](https://supabase.com/pricing) free tier
  - 500 MB Postgres DB
  - 1 GB file store
  - Unlimited API calls and users
  - built-in auth and log tables (blog.logrocket.com)
  - integrations with other services

- Firebase Firestore Spark Plan
  - NoSQL document DB
  - 1 GB stored data
  - Daily free quota: 20K document reads, 20K writes, 20K deletes

- [Cloudflare D1](https://www.cloudflare.com/developer-platform/d1/)
  - Serverless SQLite-compatible SQL DB
  - 5 GB storage/month
  - Daily free quota: 5M row reads, 100K row writes
  - No egress fees
  - [Description in logrocket blog](https://blog.logrocket.com/11-planetscale-alternatives-free-tiers/#cloudflare)
  - Cloudflare Other Choices: Cloudflare KV, Cloudflare R2 for S3-compatible object stores, Durable Objects
  - [Cloudflare Workers]( ) replaces [Cloudflare Pages](https://pages.cloudflare.com/). [Deploying React with Cloudflare Pages](https://blog.logrocket.com/deploying-react-app-full-stack-cloudflare-pages/).
    - Direct deployment from Github

- [CockroachDB](https://www.cockroachlabs.com/pricing/) free tier
  - 10 GB storage
  - 50 M requests/mo
  - Available on GCP and AWS
  - daily and hourly backups
  - PostgreSQL compatible distributed database

- [Tembo](https://tembo.io/pricing/) open-source serverless platform for Postgres. Free tier includes:
  - unlimited databases
  - 5 GB stores
  - 0.25 vCPU and 1 GB memory
  - unlimited reads and writes
  - 30-day log retention

- [Convex](https://www.convex.dev/plans) described as similar to Supabase. Free tier features:
  - 2 developers
  - 5 projects
  - 1 M function calls
  - 20 GB-hours action-compute
  - 0.5 GB database storage

- [AstroDB](https://astro.build/db/) works only with web sites built with Astro.
  - See [Astro DB on logrocket blog](https://blog.logrocket.com/11-planetscale-alternatives-free-tiers/#astro-db)




  

---

[11 Alternatives to Planetscale](https://blog.logrocket.com/11-planetscale-alternatives-free-tiers/) blog on logrocket.com describes free cloud database services.
  - 

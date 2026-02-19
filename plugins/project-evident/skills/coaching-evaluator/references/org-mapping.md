# Organization Data Mapping

Unified reference for all Project Evident coaching clients. Every skill uses this same file.

## Client Pages & Essentials

| Organization | Short Name | Folder Name | Clients DB Page ID | Essentials DB Page ID | Implementation Plan ID |
|-------------|-----------|-------------|-------------------|----------------------|----------------------|
| Ayudando Latinos a Soñar | ALAS | ALAS Working Files | 2aaa2a956650803b93c4e9565fb80dcd | cbafaee4b7334746988ea76d39f7e9ed | 2afa2a956650806cafdae445c180bdf7 |
| Building Promise USA | Building Promise | Building Promise Working Files | 2aaa2a95665080f9b43ae92cb493c43a | 20f0abcb1b914e43aab9cc267df71d1c | 2afa2a95665080c48553cdc3bcd5a7f6 |
| Chinese Progressive Association | CPA | CPA Working Files | 2aaa2a956650806cb479c164b64829ce | a7eab654617c4031bef40af65822c007 | 2afa2a9566508007b15fd1b0e17c6c93 |
| Community Housing Dev Corp | CHDC | CHDC Working Files | 2aaa2a9566508060a6d1d2ed3056e050 | cb71fd8d747a4ae6b37583cdf962fc6d | 2afa2a95665080fd84a7cc2630cbd549 |
| E4 Youth | E4 | E4 Youth Working Files | 2aaa2a95665080108e87ff952a656af6 | a6b5553660124314b0394168503922e4 | 2afa2a956650800cbd08e871236305c5 |
| Eviction Defense Collaborative | EDC | EDC Working Files | 2aaa2a956650809ca20acc03b583ddb7 | 01c62bde3bb6431eb10af51987b40546 | 2afa2a95665080ef9b34c6e9e7bf2da9 |
| Latin America Association | LAA | LAA Working Files | 2aaa2a95665080059938e10f32c53166 | 5e9704da19594e1dbcbd16d7b667c0f1 | 2afa2a95665080729058c8222c42a84e |
| Silicon Valley at Home | SV@Home | SV@Home Working Files | 2aaa2a95665080feb633f5e9e53fa702 | 10a3c22b981b4de4baedddb2d844c63f | 2afa2a9566508068972be251aabc3bd7 |
| Sumter United Ministries | Sumter | Sumter Working Files | 2aaa2a95665080fb95e5c8a03cf41175 | bc1e39451152408e8492d94af6a68ffa | 2afa2a956650800086a9d85f05c18bb9 |
| Texas Advocacy Project | TAP | TAP Working Files | 2aaa2a95665080e38fecc2f37c05d4b3 | 5f99201e619e4c6688d2df2bd5be842b | 2afa2a9566508032bc8fc6aa47521765 |
| Transgender Intersex Justice Project | TIP | TIP Working Files | 2aaa2a95665080efb5bcdfb78b3df0d2 | f41fb0c3396d4a63aa13bb9b591bf9ee | 2afa2a956650804caccec2978461de60 |

## Databases

| Database | ID / Data Source |
|----------|-----------------|
| Clients DB (Coaching) | `2aaa2a9566508079a6b2e8ee0b645c85` |
| Clients DB Data Source | `collection://2aaa2a95-6650-801d-9ea4-000b667974a3` |
| Essentials Endpoint Map | `2d1a2a95665080ee9721f7a42a03eeba` |
| Essentials Data Source | `collection://2d1a2a95-6650-80a0-aa11-000bfa5ec6d8` |
| Meeting Transcripts | `collection://669e7e0b-dfe6-43c4-b4c3-d7b734e06ed5` |

## Artifact Root Path

```
~/Dev/claude-cowork/Clients/Project Evident Updates/
```

## Access Pattern

1. Look up client → get Clients DB Page ID, Essentials DB Page ID, Folder Name
2. Fetch Clients DB page → get Coaching Calls relation → coaching call page IDs
3. Fetch each coaching call → read transcript content
4. Write artifacts to `{Artifact Root}/{Folder Name}/` subfolders
5. Write extracted data to Essentials DB page using the Essentials DB Page ID

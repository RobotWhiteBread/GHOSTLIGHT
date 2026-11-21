# GHOSTLIGHT Phase 1: trait distribution

Rules: `great-plains-1850-1930` version 1, 32 rules. Sample of 20 drawn from seed `phase1`.

## The twenty

| # | kind | region | era | origin | manifestation | disposition | condition | remedy |
|---|---|---|---|---|---|---|---|---|
| 1 | light | dakota | settled | prairie_fire | ball_light | misleading | wind_drops | do_not_follow |
| 2 | haunt | platte | trail | well_cavein | knocking | vengeful | stock_after_dark | proper_burial |
| 3 | light | dakota | settled | frozen_blizzard | meadow_lights | territorial | windmill_stops | proper_burial |
| 4 | spirit | dakota | homestead | grasshopper_year | fire_line | vengeful | lamp_unlit | salt_sill |
| 5 | revenant | flint_hills | dry_years | well_cavein | knocking | warning | haying | lamp_window |
| 6 | revenant | dakota | dry_years | searcher | cold_patch | territorial | lamp_unlit | pray_for_soul |
| 7 | revenant | sandhills | homestead | frozen_blizzard | voice | warning | anniversary | marked_grave |
| 8 | spirit | dakota | hard_winters | broken_sod | ground_blizzard | mournful | before_blizzard | three_kings |
| 9 | haunt | flint_hills | trail | claim_quarrel | bell_ringing | territorial | windmill_stops | stop_mill |
| 10 | haunt | sandhills | homestead | bone_pile | bell_ringing | vengeful | windmill_stops | cross_water |
| 11 | light | sandhills | homestead | prairie_fire | ball_light | warning | lamp_unlit | salt_sill |
| 12 | spirit | flint_hills | trail | third_dry_summer | fire_line | mournful | smoke_haze | fireguard |
| 13 | haunt | flint_hills | trail | rail_accident | cold_patch | mournful | anniversary | return_it |
| 14 | haunt | dakota | trail | sod_collapse | phantom_team | warning | before_blizzard | lamp_window |
| 15 | haunt | high_plains | homestead | sod_collapse | wrong_water | territorial | haying | salt_sill |
| 16 | light | dakota | dry_years | wet_meadow | lantern | mournful | windmill_stops | do_not_follow |
| 17 | haunt | platte | hard_winters | blizzard_school | bell_ringing | warning | crusted_snow | three_kings |
| 18 | haunt | sandhills | dry_years | blizzard_school | returns | warning | windmill_stops | salt_sill |
| 19 | revenant | platte | settled | well_cavein | knocking | vengeful | threshing | school_bell |
| 20 | spirit | high_plains | hard_winters | prairie_fire | fire_line | mournful | asks_the_way | do_not_follow |

## Spread per trait

Coverage is how many of the possible values turned up. Evenness is entropy over the values that exist (1.0 is perfectly even, 0 is one value every time).

| trait | coverage | evenness | most common |
|---|---|---|---|
| kind | 4/4 | 0.96 | haunt (8), light (4), spirit (4) |
| region | 5/6 | 0.85 | dakota (7), flint_hills (4), sandhills (4) |
| era | 5/5 | 0.98 | trail (5), homestead (5), dry_years (4) |
| community | 9/11 | 0.84 | anglo (5), swedish (4), czech (3) |
| origin | 13/24 | 0.77 | prairie_fire (3), well_cavein (3), frozen_blizzard (2) |
| manifestation | 12/19 | 0.80 | knocking (3), fire_line (3), bell_ringing (3) |
| disposition | 5/6 | 0.84 | warning (6), mournful (5), vengeful (4) |
| conditions | 11/15 | 0.82 | windmill_stops (5), lamp_unlit (3), haying (2) |
| signs | 19/21 | 0.91 | coyotes_hush (6), horses_balk (6), clock_stops (5) |
| remedy | 12/20 | 0.78 | salt_sill (4), do_not_follow (3), proper_burial (2) |

## Too tight?

- Mean pairwise similarity across all traits: **0.13** (0 shares nothing, 1 is identical).
- Most similar pair: #2 and #19 at 0.42.
- Distinct origin and manifestation pairings: 17 of 20.
- Dead ends while drawing: 0 restarts for 20 entities.

## Too loose?

Of 5000 entities drawn with every rule ignored, **4 (0.08%)** would pass. That is how much work the rules do: a random draw from the lists almost never reads as coherent folklore.

Share of random draws each rule rejects:

| rule | rejects | name |
|---|---|---|
| R14 | 68% | The signs echo the origin or the manifestation |
| R02 | 65% | Manifestation suits the kind of entity |
| R01 | 61% | Origin suits the kind of entity |
| R04 | 56% | The community lives in this country |
| R27 | 41% | The remedy answers something about it |
| R17 | 40% | The summoning condition belongs to the story |
| R30 | 27% | No sign contradicts the summoning condition |
| R15 | 24% | No sign contradicts the origin |
| R03 | 24% | The country has what the origin needs |
| R05 | 23% | The remedy belongs to the people who use it |
| R31 | 18% | The signs do not contradict one another |
| R20 | 16% | Disposition fits the origin |
| R16 | 15% | No sign contradicts the manifestation |
| R29 | 15% | The manifestation suits the hour and season of its summoning |
| R08 | 15% | The origin is possible in the era |
| R18 | 14% | No condition contradicts the origin |
| R22 | 11% | Some remedies need a particular kind of origin |
| R23 | 11% | A friendly thing is answered with courtesy, not wards |
| R28 | 10% | Some remedies need something particular in the story |
| R21 | 9% | Only lights and spirits lead travelers astray |
| R13 | 8% | Some manifestations need a particular kind of death |
| R12 | 7% | Manifestation does not contradict the origin |
| R24 | 6% | A hostile thing is not answered with courtesy |
| R25 | 6% | A misleading light is refused, not appeased |
| R09 | 5% | The community had arrived by the era |
| R26 | 3% | The remedy does not contradict the origin |
| R07 | 3% | The condition can occur in this country |
| R32 | 3% | The country was settled by the era |
| R19 | 3% | Some conditions need a particular kind of origin |
| R06 | 2% | The remedy can be carried out in this country |
| R10 | 1% | The manifestation is possible in the era |
| R11 | 1% | The remedy is possible in the era |

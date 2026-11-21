# Attention-head behavior inventory

A research seed list for symbolic attention experiments. Numbers identify entries in this catalog, not model head indices. This is a selective inventory of behaviors, not a complete decomposition of any model, and it does not assign these roles to Qwen3-0.6B.

Current size: **1,024 entries from 134 sources**. The latest researched batch is **941–1024**, completing the catalog target. These counts include physical head instances, task-conditioned behaviors, and head families; they do not imply 1,024 distinct algorithms or independently interpreted physical heads.

## Reading the examples

- **All examples below are newly composed illustrations, not measured attention traces.** They show how to recognize a proposed behavior; the cited studies establish the behavior on their own examples and datasets.
- `⟦word⟧` marks the query position: the position doing the attending. *Italics* mark the source it would attend to under the illustrated behavior. In a self-attention example, these overlap.
- `→ word` shows an illustrative completion; it is outside the input. `…` abbreviates intervening text. Word boundaries simplify actual subword tokenization.
- **Unknown** means the cited evidence does not establish the semantic payload or downstream causal effect. It does not mean there is no effect.
- Feature-association tables use a different convention: italics mark **feature cues**, because their sources do not establish token-to-token routing for those entries. Section notes identify these cases.

“Transmitted feature” describes an interpreted signal in the head's output, not a literal symbolic field. Attention weights select source representations; the value and output transformations determine what is written. Source representations may already contain information gathered elsewhere. [Transformer Circuits framework][F]

## Retrieval patterns and mechanisms

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 1 | **Current-position attention:** reads its own position. [HeadVis][H] | The latch *⟦clicked⟧* | Mira felt *⟦cold⟧* | Unknown from the attention pattern alone; reads the current contextual representation. | Unknown; a diagonal pattern does not imply an identity operation. |
| 2 | **Previous-token attention:** reads one position back. [Framework][F] | Mira *opened* ⟦the⟧ | The *river* ⟦flows⟧ | In induction circuits, information identifying the preceding token. | Lets a later head match a source position using its predecessor. |
| 3 | **Induction:** reads what followed an earlier match. [Framework][F] | copper *bell* … ⟦copper⟧ → bell | quiet *garden* … ⟦quiet⟧ → garden | Evidence for the earlier continuation. | Promotes that continuation. The source is **bell**, not the earlier **copper**. |
| 4 | **Duplicate detection:** reads an earlier occurrence of the current token. [IOI][I] | *Mira* … ⟦Mira⟧ | *lantern* … ⟦lantern⟧ | In the studied IOI circuit, evidence supports a signal identifying the earlier occurrence's position; the exact encoding was unresolved. | Helps subsequent heads distinguish the repeated subject from the other person. |
| 5 | **Long-prefix induction:** GPT-2 H5.1. [SAE study, §4.2][M] | old red *boat* … old ⟦red⟧ → boat | small brass *bell* … small ⟦brass⟧ → bell | Continuation evidence. | Promotes continuation after a longer match. |
| 6 | **Name mover:** retrieves the intended recipient in IOI. [IOI][I] | *Lena* and Theo met. Theo gave a key ⟦to⟧ → Lena | Omar and *Nia* met. Omar passed a cup ⟦to⟧ → Nia | Name identity in a direction promoting that name. | Raises the recipient name's logit. |
| 7 | **Negative name mover:** retrieves names but writes against them. [IOI][I] | *Lena* and Theo met. Theo gave a key ⟦to⟧ | Omar and *Nia* met. Omar passed a cup ⟦to⟧ | A direction opposing the attended name. | Lowers that name's logit; can oppose the correct answer on this task. |
| 8 | **Subject inhibition:** reads the repeated subject. [IOI][I] | Lena and Theo met. *Theo* gave a key ⟦to⟧ | Omar and Nia met. *Omar* passed a cup ⟦to⟧ | Subject identity and information about its earlier position. | Changes later name movers' queries so they attend less to the earlier subject. |
| 9 | **Copy suppression:** GPT-2 L10H7 retrieves a token already being overpredicted. [Copy suppression][C] | *Mira* checked the latch. It was ⟦still⟧ …; assume earlier components overpredict “Mira” | *boat* … The sailor climbed ⟦aboard⟧ …; assume earlier components overpredict “boat” | A direction opposing the retrieved token. | Reduces its logit; the study connects this to better calibration. This is not a universal repetition ban. |
| 10 | **Long-context retrieval:** reads answer-bearing context. [Retrieval heads][R] | The access word is *cobalt*. … The access word ⟦is⟧ → cobalt | Mina lives in *Oslo*. … Mina lives ⟦in⟧ → Oslo | Answer information; a complete symbolic decomposition of the payload is not established. | Supports contextual retrieval. Ablating these heads impaired retrieval in the studied models. |
| 11 | **Attention sink:** allocates attention to initial positions, even without relevant meaning. [StreamingLLM][S] | *BOS* … the lantern ⟦flickered⟧ | *BOS* … Mira opened the ⟦gate⟧ | No single semantic payload established. | Keeping initial tokens available stabilizes streaming generation in the study; semantic relevance is unnecessary. |
| 12 | **Successor:** reads an ordered item and promotes its successor. [Successor heads][O] | *4*) rope; next item ⟦:⟧ → 5 | *Tuesday*; the next day ⟦was⟧ → Wednesday | A transformed representation favoring the next item; examined through OV analysis. | Raises successor-token scores across several kinds of ordered sequence. |
| 13 | **Acronym behavior:** a studied successor head also reads acronym-relevant words. [Successor heads, §4.1][O] | United *Nations* ⟦(⟧ → UN | European *Union* ⟦(⟧ → EU | Exact intermediate feature unresolved. | Observed contribution to acronym prediction; distinct from ordinary incrementation. |
| 14 | **Greater-than behavior:** a successor head can favor later ordered items without exactly incrementing. [Successor heads, §4.1][O] | Ranked *second* before, now ranked ⟦only⟧ → fourth | From *3* up to ⟦roughly⟧ → 7 | Exact intermediate feature unresolved. | Supports a higher ordered value; does not by itself specify which higher value. |

The condition written into row 9 matters: an earlier occurrence alone is insufficient to diagnose copy suppression. Similarly, successorship, copying, and acronym behavior need not belong to separate physical heads. [Copy suppression][C]; [Successor heads][O]

## Syntax and positional patterns in BERT

**BERT is bidirectional:** future targets below are available during encoding, unlike causal next-word generation. These are attention observations, not decoded OV algorithms. Head labels follow the paper. [BERT analysis][B]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 15 | Next token; 3-1. [B] | ⟦red⟧ *boat* | ⟦brass⟧ *bell* | Unknown | Unknown |
| 16 | Broad attention; 1-1. [B] | ⟦Mira⟧ *opened the gate* | ⟦Theo⟧ *carried a lantern* | Distributed mixture | Unknown |
| 17 | Separator; 8-7. [B] | ⟦Mira⟧ left *[SEP]* | ⟦Rain⟧ fell *[SEP]* | Unknown | Possible no-op; hypothesis |
| 18 | Periods; 11-6. [B] | Rain fell *.* ⟦Mira⟧ waited. | Theo left *.* ⟦Nia⟧ stayed. | Unknown | Unknown |
| 19 | Determiner → noun; 8-11. [B] | ⟦the⟧ *lantern* | ⟦a⟧ *boat* | Unknown | Unknown |
| 20 | Object → verb; 8-10. [B] | *opened* the ⟦gate⟧ | *carried* a ⟦basket⟧ | Unknown | Unknown |
| 21 | Preposition → object; 9-6. [B] | ⟦under⟧ the *bridge* | ⟦inside⟧ the *box* | Unknown | Unknown |
| 22 | Possessive → noun; 7-6. [B] | ⟦her⟧ *lantern* | ⟦his⟧ *coat* | Unknown | Unknown |
| 23 | Passive auxiliary → verb; 4-10. [B] | ⟦was⟧ *repaired* | ⟦were⟧ *hidden* | Unknown | Unknown |
| 24 | Mention → antecedent; 5-4. [B] | *Mira* smiled. ⟦She⟧ waved. | *Theo* arrived. ⟦He⟧ sat. | Unknown | Unknown |

For our generator, a future-facing relation would need a different implementation: for example, an unfinished determiner phrase could constrain upcoming nouns. That would be our adaptation, not the measured BERT mechanism.

## Additional feature families from Appendix M

These are **SAE output-feature associations**, with heuristic head attribution. **Italic text marks illustrative cues, not verified attention targets.** “Associated” does not establish a complete transmitted representation. [Appendix M][M]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 25 | GPT-2 H0.9 [M] | *1.* bread | *2.* cheese | Associated: list context | Unknown |
| 26 | GPT-2 H2.3 [M] | *each* cup | *both* doors | Associated: quantification | Unknown |
| 27 | GPT-2 H2.5 [M] | *beneath* branches | *between* houses | Associated: spatial relations | Unknown |
| 28 | GPT-2 H3.11 [M] | *third* attempt | *entire* village | Associated: order/totality | Unknown |
| 29 | GPT-2 H6.7 [M] | *ferns* grew | *moss* spread | Associated: vegetation | Unknown |
| 30 | GPT-2 H7.5 [M] | *aunt* arrived | *cousin* waved | Associated: kinship | Unknown |
| 31 | GPT-2 H7.9 [M] | *because* rain | *therefore* wait | Associated: justification | Unknown |
| 32 | GPT-2 H8.5 [M] | *either* path | *neither* door | Associated: paired constructions | Unknown |
| 33 | GPT-2 H8.8 [M] | *longer* journey | *fewer* baskets | Associated: comparison | Unknown |
| 34 | GPT-2 H10.1 [M] | *soft* clay | *full* jar | Associated: physical attributes | Unknown |
| 35 | GPT-2 H10.4 [M] | 09*:*45 | 17*.* item | Associated: numeric separators | Unknown |
| 36 | GPT-2 H10.5 [M] | *had* departed | *would* return | Associated: tense/counterfactuals | Unknown |

## Expansion: 100 additional entries (37–136)

Added 2026-11-04, drawing on 26 additional primary research sources. These are **100 behavior entries, not 100 independently established head types**. Some are task variants, circuit roles, or recovered features. A physical head can appear in several roles.

Evidence labels in the description column:

- **R** — reported attention pattern or association; the causal algorithm may remain unknown.
- **C** — interventions support the role in the studied task; this does not validate our invented examples or every detail of the proposed mechanism.
- **F** — output-feature or representation association; italics mark cues unless a route is explicitly given.
- **T** — small task-trained model, extracted program, or constructed circuit studied in that setting.
- **Variant** — a specialization or operating regime of an existing family, not a claim of a new independent mechanism.

All new examples remain illustrative. Mathematical arrows and abbreviated prompts compress the research templates; they are not exact inputs used in experiments. Tokens can carry accumulated information absent from their surface spelling. Where we only know a circuit-level result, the row says so.

### Fuzzy matching and selective retrieval

HeadVis cases in Claude Haiku 3.5. Variants share a family. In exclusion rows, italics mark the preferred outsider, not the suppressed item. List labels and year token splits are schematic. [HV]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 37 | R · Rhyme-conditioned induction [HV] | sea *↵* … ⟦tea⟧ | blue *↵* … ⟦true⟧ | Newline evidence | Promotes newline |
| 38 | R · Cross-language induction; variant [HV] | cat *sleeps* … ⟦chat⟧ | dog *runs* … ⟦chien⟧ | Unknown | Unknown |
| 39 | R · Antonym matching; variant [HV] | hot *water* … ⟦cold⟧ | early *train* … ⟦late⟧ | Unknown | Unknown |
| 40 | R · Corresponding list positions; variant [HV] | 1. *pear* … ⟦a.⟧ | 2. *plum* … ⟦b.⟧ | Unknown | Unknown |
| 41 | R · Kinship matching; variant [HV] | aunt *arrived* … ⟦uncle⟧ | mother *waited* … ⟦father⟧ | Unknown | Unknown |
| 42 | R · Year-fragment linking [HV] | *1* ⟦742⟧ | *1* ⟦825⟧ | Unknown | Unknown |
| 43 | R · Newline-to-newline width [HV] | *↵* moss grows ⟦↵⟧ | *↵* birds sing ⟦↵⟧ | Line width | Formatting |
| 44 | R · Dialogue entity selection [HV] | *Mira*: Hi. Theo: Hello. ⟦↵⟧ | *Nia*: Yes. Omar: Fine. ⟦↵⟧ | Selected content | Copies content |
| 45 | R · Country/city exclusion [HV] | Lyon, *Oslo*: ⟦France⟧ | Milan, *Lima*: ⟦Italy⟧ | Unknown | Unknown |
| 46 | R · Continent/country exclusion; variant [HV] | Spain, *Peru*: ⟦Europe⟧ | Nepal, *Canada*: ⟦Asia⟧ | Unknown | Unknown |

### Features recovered by multitoken transcoders

These are preliminary replacement-model features, not six identified physical heads. Italics mark cues; routing is schematic. [MT]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 47 | F · Numeric outlier [MT] | 1 1 *2* 1 ⟦1⟧ | 0 *3* 0 0 ⟦0⟧ | Outlier-sensitive feature | Unknown |
| 48 | F · Broken code pattern; outlier variant [MT] | a(); a(); *b();* ⟦a();⟧ | x=1; x=1; *x=9;* ⟦x=1;⟧ | Pattern-break feature | Unknown |
| 49 | F · Sentiment negation [MT] | *unpleasant* … *not* | *awful* … *not* | Valence changes sign | Unknown |
| 50 | F · Clause position [MT] | After dusk, *we* | Because it rained, *she* | Clause-location features | Unknown |
| 51 | F · Delimiter prediction [MT] | *(* value | *[* item | Delimiter-associated cluster | Unknown |
| 52 | F · Code-context induction [MT] | load(*path*) … ⟦load(⟧ | save(*file*) … ⟦save(⟧ | Induction-associated cluster | Unknown |

### Additional syntax and lexical salience

Observed in translation encoders, which can look ahead. Adverb links are weak: the reported best heads only modestly beat positional baselines. [VO]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 53 | R · Rare-word selector [VO] | A *quokka* ⟦appeared⟧ | The *orogeny* ⟦ended⟧ | Unknown | Unknown |
| 54 | R · Verb → subject [VO] | *Mira* ⟦sang⟧ | *Theo* ⟦waited⟧ | Unknown | Unknown |
| 55 | R · Subject → verb [VO] | ⟦Mira⟧ *sang* | ⟦Theo⟧ *waited* | Unknown | Unknown |
| 56 | R · Verb → object [VO] | ⟦carried⟧ the *jar* | ⟦opened⟧ the *gate* | Unknown | Unknown |
| 57 | R · Adjective → noun [VO] | ⟦wooden⟧ *gate* | ⟦blue⟧ *jar* | Unknown | Unknown |
| 58 | R · Adverb → verb; weak association [VO] | *walked* ⟦slowly⟧ | *sang* ⟦softly⟧ | Unknown | Unknown |

### Combining word pieces

Sparse translation-encoder attention; token splits are illustrative. Both rows are behaviors of the same merging family. [SP]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 59 | R · Subword-cluster pooling [SP] | *garden* *⟦ing⟧* | *hope* *⟦ful⟧* | Pooled word-piece information | Makes combined information available |
| 60 | R · Hyphenated-unit pooling; variant [SP] | *well* *-* *⟦known⟧* | *ice* *-* *⟦cold⟧* | Pooled compound information | Makes combined information available |

### Relation-sensitive output promotion

Relation probes in Pythia: attended inputs can promote related outputs. These are relation-level variants, not eight universal head classes. Italics mark the input entity; arrows show the tested kind of output association, not a guaranteed completion. [SI]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 61 | F · Part → whole [SI] | *petal* → flower | *wheel* → bicycle | Related-token evidence | Promotes related output |
| 62 | F · Whole → part; reverse variant [SI] | *flower* → petal | *bicycle* → wheel | Related-token evidence | Promotes related output |
| 63 | F · Instrument → use [SI] | *knife* → cut | *pen* → write | Related-token evidence | Promotes related output |
| 64 | F · Entity → property [SI] | *snow* → white | *lemon* → sour | Related-token evidence | Promotes related output |
| 65 | F · Specific → general category [SI] | *robin* → bird | *oak* → tree | Related-token evidence | Promotes related output |
| 66 | F · General → specific; reverse variant [SI] | *bird* → robin | *tree* → oak | Related-token evidence | Promotes related output |
| 67 | F · Subject → plausible verb [SI] | *birds* → fly | *dogs* → bark | Related-token evidence | Promotes related output |
| 68 | F · Verb → plausible object [SI] | *drink* → water | *read* → book | Related-token evidence | Promotes related output |

### Factual attributes and argument passing

Factual recall studies distinguish attribute extraction from merely copying an entity's spelling. The first four rows concern Pythia/GPT-family mechanisms. Sports and geography are category variants. [FA]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 69 | C · Sports-attribute extraction [FA] | *Serena Williams* plays the sport ⟦of⟧ | *Lionel Messi* plays the sport ⟦of⟧ | Sport-related attributes | Promotes sports vocabulary |
| 70 | C · Geographic-attribute extraction; variant [FA] | *Colosseum* is located ⟦in⟧ | *Taj Mahal* is located ⟦in⟧ | Geographic attributes | Promotes associated places |
| 71 | C · Relation-category extraction [FA] | Spain's *capital* ⟦is⟧ | Italy's *capital* ⟦is⟧ | Candidate cities, partly subject-independent | Broadens city candidates |
| 72 | C · Mixed subject/relation extraction [FA] | *Spain*'s *capital* ⟦is⟧ | *Italy*'s *capital* ⟦is⟧ | Both attribute sources | Adds evidence to answer logits |
| 73 | C · Topic argument passed to MLP [AR] | The capital of *Norway* ⟦is⟧ | The capital of *Italy* ⟦is⟧ | Topic identity | Feeds factual transformation in MLPs |
| 74 | R · Initial-token frequency prior [AR] | *BOS* … Norway's capital ⟦is⟧ | *BOS* … Italy's capital ⟦is⟧ | Common-token directions in some late heads | Authors hypothesize reduced answer confidence |

### Sentiment and character mood

GPT-2 review circuits and Pythia mood-story circuits. A neutral word or comma can carry previously accumulated sentiment. [SE]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 75 | C · Direct adjective reader [SE] | *lovely* … verdict ⟦is⟧ | *dreary* … verdict ⟦is⟧ | Sentiment | Shifts evaluation |
| 76 | C · Direct preference-verb reader; variant [SE] | *adored* it … verdict ⟦is⟧ | *hated* it … verdict ⟦is⟧ | Sentiment | Shifts evaluation |
| 77 | C · Review-summary writer [SE] | *lovely* … This ⟦movie⟧ | *dreary* … This ⟦movie⟧ | Sentiment summary | Enables later reading |
| 78 | C · Review-summary reader [SE] | lovely … This *movie* ⟦is⟧ | dreary … This *movie* ⟦is⟧ | Stored sentiment | Shifts evaluation |
| 79 | C · Comma-summary → repeated name [SE] | Mira loves rain*,* … ⟦Mira⟧ | Theo hates rain*,* … ⟦Theo⟧ | Character-linked sentiment | Supplies mood evidence |
| 80 | C · Feeling-token reader [SE] | Mira … *feels* ⟦very⟧ | Theo … *feels* ⟦very⟧ | Stored mood evidence | Promotes compatible mood |

### Multiple-choice selection

Chinchilla heads; these roles can share machinery with other tasks. Amplification is the authors' interpretation, not a fully established algorithm. [MC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 81 | C · Correct-label selection [MC] | 2+2? A. five; *B*. four. Answer⟦:⟧ | 3+3? A. seven; *B*. six. Answer⟦:⟧ | Answer label | Raises selected label |
| 82 | R · Uniform label pooling [MC] | *A*. red; *B*. blue. ⟦Answer⟧ | *A*. cat; *B*. dog. ⟦Answer⟧ | Unknown | Unknown |
| 83 | R · Fixed-label preference [MC] | *A*. red; B. blue. ⟦Answer⟧ | *A*. dog; B. cat. ⟦Answer⟧ | Unknown | Unknown; may require other heads |
| 84 | R · Late answer amplification [MC] | … *Answer* *⟦:⟧* | … *choice* *⟦:⟧* | Hypothesized answer evidence | Hypothesized reinforcement |
| 85 | C · Answer-content gatherer [MC] | 2+2? A. five; B. *four*. ⟦Answer⟧ | 3+3? A. *six*; B. seven. ⟦Answer⟧ | Answer-content information | Shapes label-selector queries |

### Acronym construction

GPT-2 three-letter acronym circuit. The first three rows are generation-step variants, not separate dedicated heads. Initial-letter token boundaries are shown explicitly. [AC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 86 | C · First initial selection; variant [AC] | *C*edar River Club ⟦(⟧ → C | *B*irch Lake Group ⟦(⟧ → B | Unspaced capital letter | Starts acronym |
| 87 | C · Second initial selection; variant [AC] | Cedar *R*iver Club (⟦C⟧ → R | Birch *L*ake Group (⟦B⟧ → L | Next capital letter | Extends acronym |
| 88 | C · Third initial selection; variant [AC] | Cedar River *C*lub (C⟦R⟧ → C | Birch Lake *G*roup (B⟦L⟧ → G | Next capital letter | Completes acronym |
| 89 | C · Previous-word-initial relay [AC] | *C*edar ⟦R⟧iver Club | *B*irch ⟦L⟧ake Group | Preceding initial information | Helps select next word's initial |

### Task representations carried by heads

Function-vector task variants. Italics mark demonstration cues, not established source positions. The vector is assembled from multiple head outputs; these rows do not imply dedicated single heads for each task. [FV]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 90 | C/F · Antonym task vector; variant [FV] | *hot → cold*; tall → short | *open → closed*; young → old | Task representation | Injection can induce task execution |
| 91 | C/F · Synonym task vector; variant [FV] | *small → little*; large → big | *quick → fast*; silent → quiet | Task representation | Injection can induce task execution |
| 92 | C/F · Capitalization task vector; variant [FV] | *moss → Moss*; fern → Fern | *river → River*; lake → Lake | Task representation | Injection can induce task execution |
| 93 | C/F · Translation task vector; variant [FV] | *cat → chat*; dog → chien | *house → Haus*; book → Buch | Task representation | Injection can induce task execution |

### Translation and temporal context

Translation roles come from Llama/Vicuna analyses. Temporal-head rows are cue variants with causal evidence at head level; exact token-level routing is left unspecified. [TR] [TM]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 94 | C · Translation source reader [TR] | Chinese: *猫*. English⟦:⟧ | English: *water*. Chinese⟦:⟧ | Source-language information | Supplies downstream translation computation |
| 95 | R · Language-indicator reader [TR] | 猫; *English*⟦:⟧ | water; *中文*⟦:⟧ | Translation-mode cue | Helps condition translation |
| 96 | R · Translation separator reader; variant [TR] | Chinese*:* 猫. English⟦:⟧ | English*:* water. Chinese⟦:⟧ | Structural indicator | Boundary/mode role inferred |
| 97 | C/F · Numeric temporal cue [TM] | In *1998*, the leader … | In *2012*, the team … | Time-conditioned information; encoding incomplete | Supports time-specific recall |
| 98 | C/F · Verbal temporal cue; variant [TM] | In the *year* 1998 … | During the *year* 2012 … | Temporal-context association | Supports time-specific recall |

### Arithmetic and comparisons

Addition roles are from GPT-J; the helix descriptions are fitted representations supported by interventions. Greater-than rows are task variants of a GPT-2 circuit whose comparison is largely performed by MLPs. [AD] [GT]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 99 | C · Addition operand gatherer [AD] | *23* + *14* ⟦=⟧ | *41* + *12* ⟦=⟧ | Operand helices | Feeds downstream MLPs |
| 100 | C · Addition result reader [AD] | 23 + 14 *⟦=⟧* | 41 + 12 *⟦=⟧* | Computed-sum helix | Promotes answer through logits |
| 101 | C · Mixed arithmetic head [AD] | *23* + *14* *⟦=⟧* | *41* + *12* *⟦=⟧* | Operands and result-related signal | Feeds downstream computation |
| 102 | C · Start-year suffix reader [GT] | from 17 *41* to ⟦17⟧ | from 18 *26* to ⟦18⟧ | Start-year numeric information | MLPs favor larger suffixes |
| 103 | C · Price lower-bound reader; variant [GT] | price: $17 *41* to $⟦17⟧ | price: $17 *26* to $⟦17⟧ | Lower-bound information | Same circuit supports upper-range completion |

### In-context statistics and decompiled algorithms

Toy-trained models. Statistical rows describe learned algorithms at circuit/model level; especially the trigram result does not isolate a universal individual head. D-RASP rows describe extracted attention operations with downstream processing kept separate. [ST] [DR]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 104 | T · Contextual unigram estimator [ST] | *a b a a* ⟦?⟧ | *b c b b* ⟦?⟧ | Empirical token frequencies | Predicts a distribution |
| 105 | T · Statistical induction / bigram estimator [ST] | a *b* … a *c* … a *b* … ⟦a⟧ | x *y* … x *z* … ⟦x⟧ | Continuation frequencies | Predicts conditional distribution |
| 106 | T · Trigram estimator; circuit-level [ST] | a b *c* … a b *d* … a ⟦b⟧ | x y *z* … x y *w* … x ⟦y⟧ | Two-token-conditioned statistics | Predicts conditional distribution |
| 107 | T · Most-frequent-token pooling [DR] | *a b a a* ⟦SEP⟧ → a | *c d d d* ⟦SEP⟧ → d | Normalized histogram | Readout chooses largest component |
| 108 | T · Next-larger-item selection [DR] | 9 *5* 2; sorted: ⟦2⟧ → 5 | 8 1 *4*; sorted: ⟦1⟧ → 4 | Weighted candidate histogram | Later operation sharpens next item |
| 109 | T · Bracket-balance pooling [DR] | *BOS ( (* *⟦)⟧* | *BOS ( ) (* *⟦)⟧* | Opening/closing/BOS histogram | Thresholds govern closing or ending |

### Iterative algorithms

Two-layer iteration circuit, constructed and studied in trained toy models. The update rule lives in the MLP; the attention operations retrieve inputs. [IT]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 110 | T · Input-boundary locator [IT] | 1 0 1 *EOI* e ⟦o⟧ | 0 1 *EOI* ⟦e⟧ | EOI position | Enables computation of next input index |
| 111 | T · Indexed next-input reader [IT] | 1 *0* 1 EOI ⟦o⟧ | 0 *1* EOI ⟦e⟧ | Input at current iteration | Combines with prior state in MLP |

### Syllogistic reasoning

GPT-2 medium circuit on restricted syllogism templates. Helpful and harmful copying are both included; these are not general logical inference primitives. [SY]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 112 | C · First-premise continuation bias [SY] | A→*B*; B→C; A⟦→⟧ | D→*E*; E→F; D⟦→⟧ | Middle-term evidence | Incorrectly promotes middle term |
| 113 | C · Repeated-middle-term linkage [SY] | All A are B*.* All ⟦B⟧ are C | All D are E*.* All ⟦E⟧ are F | Earlier middle-term information at following token (inferred) | Supports suppression pathway |
| 114 | C · Middle-term suppression [SY] | A→B; *B*→⟦C⟧ | D→E; *E*→⟦F⟧ | Middle-term opposition at predicate position | Later movers relay suppression toward answer |
| 115 | C · Conclusion-predicate mover [SY] | A→B; B→*C*; A⟦→⟧ | D→E; E→*F*; D⟦→⟧ | Conclusion predicate | Promotes valid endpoint |

### Code types and counting decisions

Code examples show a later variable use retrieving an earlier type. Count01 is a deliberately tiny synthetic language: output 4 when ones outnumber zeros, otherwise 5. [CO] [CT]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 116 | R · Variable-type reader [CO] | x: *int*; print(⟦x⟧) | y: *str*; print(⟦y⟧) | Type information associated with variable | Supports type representation; generation effect unestablished |
| 117 | T · Count-difference discriminator [CT] | *1 0 1* 2 ⟦=⟧ → 4 | *0 0 1* 2 ⟦=⟧ → 5 | Count-sensitive head outputs | Separates majority cases |
| 118 | T · Counting-task termination; ensemble [CT] | 1 0 1 = *⟦4⟧* → EOS | 0 0 1 = *⟦5⟧* → EOS | Syntax-sensitive combination; exact source varies | Joint head weighting supports termination |

### Line length and formatting

Claude Haiku character-counting study. These rows describe roles or operating regimes within a distributed circuit, not four independent counters. ↵ is a newline. [LW]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 119 | C · Newline-anchored count estimate [LW] | *↵* a small ⟦bird⟧ | *↵* the old ⟦gate⟧ | Approximate character position | Seeds line-length estimate |
| 120 | C · Token-length correction [LW] | ↵ *extraordinary* *⟦trees⟧* | ↵ *tiny* *⟦ants⟧* | Correction for token lengths | Refines character count |
| 121 | C · Line-boundary comparator [LW] | prior line*↵* near the ⟦edge⟧ | prior line*↵* almost ⟦full⟧ | Characters-remaining evidence | Contributes to wrap decision |
| 122 | R · Git-diff delimiter capture [LW] | *@@* old code ⟦↵⟧ | *@@* new code ⟦↵⟧ | Alternative counting anchor | Can distort wrapping outside diff context |

### Truth values and negation

GPT-2 study using constrained binary tasks. The schematic notation means “same truth value as” (=) and “opposite truth value to” (≠), not arithmetic. [TV]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 123 | C · Truth-value copier [TV] | A=*true*; B=A; B⟦=⟧ | A=*false*; B=A; B⟦=⟧ | Truth-token direction | Promotes same value |
| 124 | C · Truth-value suppressor [TV] | A=*true*; B≠A; B⟦=⟧ | A=*false*; B≠A; B⟦=⟧ | Opposition to source truth | With MLPs enables negation |
| 125 | C · Incorrect-truth reinforcement [TV] | A=true; B=*false*; ask A⟦=⟧ | A=false; B=*true*; ask A⟦=⟧ | Incorrect truth direction | Can oppose correct conclusion |
| 126 | C · Incorrect-truth suppression [TV] | A=true; B=*false*; ask A⟦=⟧ | A=false; B=*true*; ask A⟦=⟧ | Opposition to distractor truth | Supports correct conclusion |

### Entity binding and address-based retrieval

Llama-7B circuit groups. “Position” is the study's task-specific positional signal; it need not be a general symbolic identifier. In the first row, italics mark segment cues rather than a resolved single edge. [ET]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 127 | C · Structure reader; group D [ET] | *coin is in box* ⟦A⟧ | *key is in box* ⟦B⟧ | Segment-associated information; function unresolved | Feeds position detector |
| 128 | C · Position detector; group C [ET] | coin in box *A* … box ⟦A⟧ | key in box *B* … box ⟦B⟧ | Relevant object's positional signal | Feeds transmitter |
| 129 | C · Position transmitter; group B [ET] | … box *A* contains⟦:⟧ | … box *B* contains⟦:⟧ | Object-position signal | Changes retrieval queries |
| 130 | C · Value fetcher; group A [ET] | *coin* in box A … A contains⟦:⟧ | *key* in box B … B contains⟦:⟧ | Retrieved object identity | Promotes matching object |

### Updating bindings after swaps

Recent Gemma/Llama study; these are candidate functional groups, with stronger causal support for dereferencing than for a complete decomposition. Italics in the first two rows mark the relevant binding context. [RB]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 131 | C/F · Swap-position transmitter [RB] | *A↔B*; ask A | *C↔D*; ask D | Swap-related binding information | Propagates update context |
| 132 | C/F · Updated-address dereferencer [RB] | *A↔B*; ask A → address B | *C↔D*; ask D → address C | Resolved binding/address | Routes answer retrieval |
| 133 | C · Post-swap answer retrieval [RB] | A:coin; B:*key*; swap A,B; A⟦:⟧ | C:cup; D:*hat*; swap C,D; C⟦:⟧ | Object at updated binding | Promotes updated answer |

### Code graph relations

Attention association analyses across pretrained code models and code LLMs. These are graph-relation families, not proven symbolic algorithms. Italics mark related spans; query direction and exact payload are not asserted. [CG]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known |
| --- | --- | --- | --- | --- | --- |
| 134 | R · Data-dependence association [CG] | *x=3*; *y=x+1* | *a=input()*; *print(a)* | Unknown | Unknown |
| 135 | R · Control-dependence association [CG] | *if ready:* *send()* | *while live:* *tick()* | Unknown | Unknown |
| 136 | R · Control-flow association [CG] | *step1()*; *step2()* | *try: run()*; *finally: close()* | Unknown | Unknown |

## Expansion toward 1,024: layer-resolved research entries

This batch adds **100 entries (137–236)** from 23 further primary sources, including original investigator reports and preprints. Model and layer information is included where established.

The target is **1,024 entries**; this section is being expanded in researched batches. The inventory still mixes physical head instances, behavior families, and explicitly identified circuit/feature results. Repeated instances are labeled; changing an example does not create a new algorithm. Layer numbers use each source's convention and are not comparable across models. **Unlocalized** means a layer assignment has not been established here, not that all layers implement that function.

### Negation: transporting a cue versus constructing an alternative

Layer-level mechanisms in Llama-3.1-8B; these rows do not identify isolated physical heads. Feature examples mark cues when token routing was not established. §5 separates attention contributions from later MLP amplification. [NG]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 137 | R · Negation-cue transport | *not* ⟦wooden⟧ | *not* ⟦edible⟧ | Negation signal at modified concept | Makes composition possible | Llama-3.1-8B; early layers, decodable by L4 |
| 138 | C/F · Constructive negation relay | A material *not metallic* is … | A place *not outdoors* is … | Alternative-concept evidence | Supports a compatible completion | Llama-3.1-8B; attention around L14 |
| 139 | C/F · Negated-concept suppression | A creature *not aquatic* is … | A tool *not electric* is … | Opposition to excluded concept | Weakens incompatible completions | Llama-3.1-8B; attention around L14 |
| 140 | C/F · Negation-blind shortcut | An animal *not winged* is … | A material *not transparent* is … | Positive-association bias | Can overpower negation processing | Llama-3.1-8B; attention around L17 |

### Tense and multilingual lexical copying

Individual Qwen2-0.5B-Instruct instances, not five unique algorithms. Italics indicate task cues: §4.5 establishes output roles, not each illustrated attention edge. Late MLPs also contribute to English inflection. [TS]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 141 | C/F · Past-tense preference; instance | Today I paint. *Yesterday* I also … | Now I cook. *Yesterday* I also … | Past-tense bias | Disambiguates verb tense | Qwen2-0.5B-Instruct L19H4 |
| 142 | C/F · Past-tense preference; instance | Now I dance. *Yesterday* I also … | Today I jump. *Yesterday* I also … | Past-tense bias | Disambiguates verb tense | Qwen2-0.5B-Instruct L19H5 |
| 143 | C/F · Verb-family copying; instance | Now I *walk*. Yesterday I also … | 现在我*学习*。昨天我也 … | Related verb forms | Supports lexical choice across languages | Qwen2-0.5B-Instruct L21H3 |
| 144 | C/F · Verb-family copying; instance | Now I *help*. Yesterday I also … | 现在我*工作*。昨天我也 … | Related verb forms | Supports lexical choice across languages | Qwen2-0.5B-Instruct L21H4 |
| 145 | C/F · Verb-family copying; instance | Now I *play*. Yesterday I also … | 现在我*跳舞*。昨天我也 … | Related verb forms | Supports lexical choice across languages | Qwen2-0.5B-Instruct L21H13 |

### Agreement: positional readers and intervention effects

Appendix A reports different outcomes for number-swapping and zero ablation. Fixed-position behavior should not be renamed a general subject finder. For the last two rows, italics are grammatical cues; precise routing/payload remains unresolved. [AG]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 146 | R/C · Second-word reader | The *sailor* near the boats ⟦often⟧ … | The *bakers* beside the shop ⟦usually⟧ … | Unknown; position-linked representation | Zero ablation affects agreement | GPT-2 Small L0H10 |
| 147 | R/C · Fifth-word reader | The sailor near the *boats* ⟦often⟧ … | The bakers beside the *shop* ⟦usually⟧ … | Unknown; position-linked representation | Zero ablation affects agreement | GPT-2 Small L2H8 |
| 148 | C/F · Adverse separated-agreement contribution | The *sailor* near the boats … | The *bakers* beside the shop … | Unknown | Usually negative number-swap indirect effect | GPT-2 Small L10H9 |
| 149 | C/F · Weak supportive agreement contribution | The *sailor* … | The *bakers* … | Unknown | Consistently positive but small indirect effect | GPT-2 Small L11H11 |

### Plural reference: grouping before pronoun selection

Qwen3-1.7B circuit, §5. The study also tests Qwen3-0.6B and GPT-2 Medium, without implying matching head indices. Grouping depends on conjunction and entity similarity; a coordinated noun phrase does not guarantee a plural prediction. [PL]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 150 | R/C · Pronoun-to-antecedent mapping | *Mira* arrived with ⟦her⟧ sister | *Theo* smiled because ⟦he⟧ had won | Coreference-associated information | Feeds later reference processing | Qwen3-1.7B L13H6 |
| 151 | C · Candidate plural-group formation | Theo saw *Mira and her sister*, then waved ⟦at⟧ | Mira met *Theo and his brother*, then smiled ⟦at⟧ | Plural-group signal; interpretation | Influences selection-head values | Qwen3-1.7B L17H9 |
| 152 | C · Antecedent selection; instance | Theo saw *Mira* and her *sister*, then waved ⟦at⟧ | Mira met *Theo* and his *brother*, then smiled ⟦at⟧ | Referent evidence | Affects singular/plural pronoun probability | Qwen3-1.7B L23H12 |
| 153 | C · Antecedent selection; instance | Nia saw *Omar* and *Lena*, then waved ⟦at⟧ | Omar met *Nia* and *Mira*, then smiled ⟦at⟧ | Referent evidence | Affects singular/plural pronoun probability | Qwen3-1.7B L23H13 |

### Negated factual questions: answer identity versus answer category

Gemma 3-12B-IT, §4 and Appendices E.4–E.5. Negation changes head contributions; candidate-specific promotion also involves MLPs. Italics mark evidence/category cues, not verified routes for our invented prompts. These roles can overlap within a head. [NA]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 154 | C/F · Original-answer retrieval weakened | What is not the capital of *Italy*? | What is not the capital of *Norway*? | Reduced original-answer support | Helps move away from the unnegated answer | Gemma 3-12B-IT L31H13 |
| 155 | C/F · Answer-category candidate support | What is not the *capital* of Italy? | What is not the *color* of snow? | Same-category candidate evidence | Supports alternatives without selecting one reliably | Gemma 3-12B-IT L25H8 |
| 156 | C/F · Category support with answer opposition | What is not the *capital* of Norway? | What is not the *color* of coal? | Category evidence plus answer opposition | Changes alternative-versus-original preference | Gemma 3-12B-IT L31H12 |
| 157 | C/F · Category-concept promotion | What is not the *color* of grass? | What is not the *color* of a lemon? | Category-related concept evidence | Changes alternative-versus-original preference | Gemma 3-12B-IT L26H3 |

### Maze edges: writing connectivity at separators

Task-trained models Stan and Terry, §3.1–3.3. Coordinates are tokens; examples show early-context edges. Stan's offset pattern shifts in longer contexts. Terry's four instances share a broad connectivity role; the paper does not fully separate their algorithms. [WM]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 158 | T/C · Even-parity endpoint reader | *(0,0)* ↔ (0,1) ⟦;⟧ | (1,0) ↔ *(1,1)* ⟦;⟧ | Transformed coordinate information | Contributes to edge representation | Stan L0H3 |
| 159 | T/C · Split endpoint reader | *(0,0)* ↔ *(0,1)* ⟦;⟧ | *(1,0)* ↔ *(1,1)* ⟦;⟧ | Mixture of endpoint information | Contributes to edge representation | Stan L0H5 |
| 160 | T/C · Odd-parity endpoint reader | (0,0) ↔ *(0,1)* ⟦;⟧ | *(1,0)* ↔ (1,1) ⟦;⟧ | Transformed coordinate information | Contributes to edge representation | Stan L0H7 |
| 161 | T/C · Connectivity consolidation; instance | *(2,0) ↔ (2,1)* ⟦;⟧ | *(3,0) ↔ (3,1)* ⟦;⟧ | Endpoint information; mixture varies | Contributes to edge representation | Terry L0H0 |
| 162 | T/C · Connectivity consolidation; instance | *(0,2) ↔ (1,2)* ⟦;⟧ | *(0,3) ↔ (1,3)* ⟦;⟧ | Endpoint information; mixture varies | Contributes to edge representation | Terry L0H1 |
| 163 | T/C · Connectivity consolidation; instance | *(2,2) ↔ (2,3)* ⟦;⟧ | *(3,2) ↔ (3,3)* ⟦;⟧ | Endpoint information; mixture varies | Contributes to edge representation | Terry L0H2 |
| 164 | T/C · Connectivity consolidation; instance | *(4,0) ↔ (4,1)* ⟦;⟧ | *(4,2) ↔ (4,3)* ⟦;⟧ | Endpoint information; mixture varies | Contributes to edge representation | Terry L0H3 |

### Multilingual retrieval and output-language transition

Head-set roles, not one named head per language. §3 and Figure 4 distinguish literal retrieval from cross-language correspondence. Layer ranges below describe distributions, not every member. Feature examples mark source/target correspondence without asserting an exact query token. [RT]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 165 | R/C · Retrieval shared across languages | The code is *cobalt*. Code: … | Der Code ist *Kobalt*. Code: … | Contextual answer evidence | Supports multilingual retrieval | Qwen2.5-7B-Instruct; distributed head set |
| 166 | R/C · Language-exclusive retrieval | Neno la siri ni *bahari*. Neno: … | 口令是*蓝色*。口令：… | Language-conditioned retrieval evidence | Supports retrieval in tested language | Qwen2.5-7B-Instruct; enriched in final three layers |
| 167 | C/F · Cross-language retrieval transition | The key is *silver*. La clé est … | The door is *blue*. Die Tür ist … | Cross-language correspondence; exact encoding unknown | Supports target-language generation | Qwen2.5-7B-Instruct; concentrated L14–23 |
| 168 | C/F · Retrieval transition; model replication | The box is *red*. La boîte est … | The bag is *green*. Die Tasche ist … | Cross-language correspondence; exact encoding unknown | Masking impairs multilingual reasoning/coherence | Llama-3.1-8B-Instruct; middle-layer head set |

### Multimodal function-sensitive heads

CogVSR uses probes and head interventions, not complete QK/OV algorithms. Each row is a function-associated head set across tested VLMs. Italics describe image/context cues, not literal text attention edges; exact per-function layer ranges are not asserted here. [VS]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 169 | F/C · Basic visual-feature sensitivity | Image: *blue circular token* | Image: *red square tile* | Feature-associated activations | Ablation harms basic visual judgments | Qwen2.5-VL / InternVL3 / Llama3.2-Vision; per-model heatmaps |
| 170 | F/C · Object-identity sensitivity | Image: *fox beside a chair* | Image: *cup beside a kettle* | Object-associated activations | Ablation harms semantic recognition | Same model families; per-model heatmaps |
| 171 | F/C · Spatial-configuration sensitivity | Image: *cup left of plate* | Image: *lamp above desk* | Spatial-associated activations | Ablation harms spatial judgments | Same model families; sparse head sets |
| 172 | F/C · Relational-comparison sensitivity | Image: *two aligned arrows* | Image: *two differently oriented chairs* | Relation-associated activations | Ablation harms relation judgments | Same model families; sparse head sets |
| 173 | F/C · Context-information sensitivity | Image caption: *the marked cup is mine* | Image label: *exit on the left* | Context-associated activations | Ablation harms information extraction | Same model families; per-model heatmaps |
| 174 | F/C · Knowledge-recall sensitivity | Image question about *a compass* | Image question about *a sundial* | Knowledge-associated activations | Ablation harms knowledge questions | Same model families; per-model heatmaps |
| 175 | F/C · Quantitative-operation sensitivity | Image: *three cups and two plates* | Image: *four red tiles and one blue tile* | Quantity-associated activations | Ablation harms numerical questions | Same model families; per-model heatmaps |
| 176 | F/C · Decision-stage sensitivity | Evidence: *arrow points toward target*; true/false? | Evidence: *cup is outside box*; true/false? | Decision-associated activations | Ablation harms answer selection | Same model families; per-model heatmaps |

### Question intent versus answer retrieval

[Atlas of In-Context Learning][AT], §6 and Appendix C. The first four rows are tested task variants of the same head family, not four isolated head types. Italics mark task cues except in the retrieval row.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 177 | C/F · Birth-date question intent; variant | Biography … *when born?* | Life history … *date of birth?* | Requested attribute | Patched outputs redirect answers | Llama-3.1-8B, Mistral-7B-v0.3, Gemma-2-9B instruction models; middle-layer task sets |
| 178 | C/F · Birth-place question intent; variant | Biography … *where born?* | Life history … *birthplace?* | Requested attribute | Redirects attribute selection | Same task sets |
| 179 | C/F · Education question intent; variant | Biography … *where educated?* | Life history … *which university?* | Requested attribute | Redirects attribute selection | Same task sets |
| 180 | C/F · Profession question intent; variant | Biography … *occupation?* | Life history … *profession?* | Requested attribute | Redirects attribute selection | Same task sets |
| 181 | C/F · Parametric attribute carrier | *Ada Lovelace*: occupation? | *Marie Curie*: occupation? | Entity-associated knowledge | Patching transfers attribute bias | Same models; early/late parametric sets |
| 182 | C · Answer-span copier; variant | Diary: *Silver Lantern*. Title⟦:⟧ | Notebook: *Winter Orchard*. Title⟦:⟧ | Retrieved text | Attention steering induces copying | Same models; later retrieval sets |

### Knowledge conflict: four heads with conditional effects

[Taming Knowledge Conflicts][JC], Table 1. Italics mark conflict cues, not established attention targets. Effects below are changes after zero-ablation; their signs must not be mistaken for the head's direct logit contribution. “Short” and “coherent” refer to the paper's two conflict formats.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 183 | C/F · Context-opposing contribution in both formats | Short: France's capital is *Lyon*. | Coherent fictional account: France is governed from *Lyon*. | Unknown | Ablation raises context probability in both | Gemma-2b L8H0 |
| 184 | C/F · Context-opposing contribution; second instance | Short: Italy's capital is *Milan*. | Coherent fictional account: Italy is governed from *Milan*. | Unknown | Ablation raises context probability in both | Gemma-2b L15H6 |
| 185 | C/F · Conflict-format-dependent contribution | Short: Japan's capital is *Osaka*. | Coherent fictional account: Japan is governed from *Osaka*. | Unknown | Ablation helps context on short conflicts, hurts on coherent ones | Gemma-2b L9H3 |
| 186 | C/F · Conflict-format-dependent contribution; second instance | Short: Canada's capital is *Toronto*. | Coherent fictional account: Canada is governed from *Toronto*. | Unknown | Same sign reversal | Gemma-2b L13H5 |

### Board-state transport in Othello

[Othello dictionary-circuit study][OT], §3.3. These are scoped circuit interpretations in a six-layer task-trained model. Move labels below are schematic, not legal game transcripts. For feature rows, italics mark cues.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 187 | R/F · Reads own moves | *own earlier move* … ⟦own current move⟧ | *own current move* at ⟦current position⟧ | Own-color board information | Contributes to updated board features | Othello-GPT L2H5 |
| 188 | R/F · Reads opponent moves | *opponent move* … ⟦own move⟧ | *opponent placement* … ⟦current move⟧ | Color perspective conversion | Contributes to updated board features | Othello-GPT L2H2 |
| 189 | R · Opponent-turn selector | *other player's move* … ⟦my move⟧ | *my prior move* … ⟦other player's move⟧ | Unknown; positional/turn QK features | Routes opposite-turn information | Othello-GPT L1H0 |
| 190 | F · Piece-color feature contributor | *own piece* beside a line | *opponent piece* in a line | Color-related feature contribution | Supports later flip computation | Othello-GPT L0H6 |
| 191 | F · Piece-color feature contributor; second instance | *placed piece* closes a line | *neighboring pieces* change color | Color-related feature contribution | Supports later flip computation | Othello-GPT L0H7 |

### Python docstring circuit

[Original docstring investigation][DS]. Nine roles cover eight physical heads; L1H4 appears twice. The extracted circuit is incomplete. Names and punctuation below abbreviate tokenized function definitions and successive `:param` lines.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 192 | R · Previous-token helper | *param* ⟦width⟧ | *param* ⟦depth⟧ | Predecessor information | Supports induction | attn-only-4l L0H2 |
| 193 | C · Position via BOS dilution | *BOS* … param ⟦width⟧ | *BOS* … param ⟦depth⟧ | Position-related magnitude | Favors recent argument | attn-only-4l L0H4 |
| 194 | C · Embedding transformer | def f(*⟦width⟧*, height) | def g(*⟦depth⟧*, count) | Transformed token embedding | Supports downstream matching | attn-only-4l L0H5 |
| 195 | C · Argument-to-comma relay | def f(width, *height* ⟦,⟧ depth) | def g(red, *green* ⟦,⟧ blue) | Previous argument | Prepares next relay | attn-only-4l L1H4 |
| 196 | C · Comma-to-next-argument relay | def f(width, height *,* ⟦depth⟧) | def g(red, green *,* ⟦blue⟧) | Predecessor carried at comma | Prepares answer key | attn-only-4l L2H0 |
| 197 | C · Recent docstring-argument induction | param width … param *height* … ⟦param⟧ | param red … param *green* … ⟦param⟧ | Last documented argument | Guides answer lookup | attn-only-4l L1H4 |
| 198 | C · Duplicate/BOS competition | *BOS* … *width* … ⟦width⟧ | *BOS* … *depth* … ⟦depth⟧ | BOS-dependent output | Biases movers toward definitions | attn-only-4l L1H2 |
| 199 | C · Definition argument mover | f(width,height,*depth*); param height … ⟦param⟧ | g(red,green,*blue*); param green … ⟦param⟧ | Argument identity | Promotes next name | attn-only-4l L3H0 |
| 200 | C · Definition argument mover; second instance | f(a,b,*count*); param b … ⟦param⟧ | g(x,y,*size*); param y … ⟦param⟧ | Argument identity | Promotes next name | attn-only-4l L3H6 |

### More behaviors of one polysemantic code head

[Polysemantic attention-head follow-up][PS]. All three entries concern the same L1H4. `NL+N` means a newline token with N spaces; this is schematic tokenization. The arithmetic observation was exploratory, without a demonstrated arithmetic algorithm.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 201 | C · Reads a larger indentation level | *NL+8* return x … ⟦NL+4⟧ | *NL+12* return y … ⟦NL+8⟧ | Unknown | BOS replacement harms tested completions | attn-only-4l L1H4 |
| 202 | R · Mixed local and induction routing | NL+4 *return* … *x* ⟦NL+4⟧ | NL+8 *yield* … *y* ⟦NL+8⟧ | Unknown | Unknown for this mixture | attn-only-4l L1H4 |
| 203 | R · Recent arithmetic-token preference; tentative | width = height *+* border … ⟦width⟧ | area = length *×* width … ⟦area⟧ | Unknown | Unknown | attn-only-4l L1H4 |

### Mechanisms exposed by weight sparsity

[Weight-sparse transformers][WS], §3.2 and Appendix F.2. These models were trained for interpretability; their circuits are not established mechanisms of arbitrary dense LMs. Bracket averaging is length-sensitive, not an exact stack. Model variants differ between tasks.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 204 | C · Quote-type retrieval | print*("*⟦winter⟧ → ") | print*('*⟦summer⟧ → ') | Opening quote type | Favors matching closer | Sparse model L10H82 |
| 205 | C · Open-bracket density averaging | values = *[* 2, 4 ⟦end⟧ | values = *[* *[* 2, 4 ⟦end⟧ | Averaged bracket-detector value | Feeds nesting threshold | Sparse model L2H125 |
| 206 | C/F · Nesting softmax threshold | values = *[[* 3, 6 … | values = *[* 3, 6 … | Thresholded depth signal | Favors double closing bracket | Sparse model L4H80 |
| 207 | C · Variable-name-to-type-site relay | *current* = ⟦set()⟧ | *current* = ⟦""⟧ | Variable identity | Makes type site addressable | Sparse model L4H73 |
| 208 | C · Type-site lookup | current = *set()* … ⟦current⟧ | current = *""* … ⟦current⟧ | Type-associated information | Supports type-dependent completion | Sparse model L6H26 |
| 209 | R/F · Redundant bracket counter | items = *[* 1, 5 … | items = *[[* 1, 5 … | Bracket-density information | Parallel contribution; pruned for simplicity | Sparse model L3H85 |

### Routing an intermediate entity in multilingual reasoning

[Bridge Routing Heads][BR], §4 (preprint). These are head-set roles. Bridge identity was decoded from layer states, not isolated head values. Italics mark question cues; no particular source token is established. Model replications remain the same broad mechanism.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 210 | C/F · Shared bridge-routing pool | Capital of *Shakespeare's birth country*? | Capital of *Mozart's birth country*? | Chaining-related output; exact head payload unknown | Pool ablation harms two-hop answers | Llama-3.1-70B; concentration L14–38 |
| 211 | C/F · Language-specific bridge-routing pools | Capital del país de nacimiento de *Shakespeare*? | Capital del país de nacimiento de *Mozart*? | Language-conditioned chaining signal | Pool scaling improves some failures | Llama-3.1-70B; midlayers, Japanese late tail |
| 212 | C/F · Shared bridge-routing pool; replication | Capital of *Cervantes's birth country*? | Capital of *Dante's birth country*? | Chaining-related output; exact head payload unknown | Pool ablation harms two-hop answers | Qwen2.5-72B; concentration L47–57 |
| 213 | C/F · Language-specific bridge-routing pools; replication | *莎士比亚*出生国的首都是哪里？ | *莫扎特*出生国的首都是哪里？ | Language-conditioned chaining signal | Pool scaling improves some failures | Qwen2.5-72B; concentration L47–57 |

### Agreement contrasts across languages

[Shared Circuits for Shared Grammar][SG], §3–5 (preprint). Four experimental contrasts, not four independent head types. Italics mark pronoun cues. Output patching supports agreement contributions but does not decode symbolic person/number fields.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 214 | C/F · First versus second person singular; variant | hablar: *yo* → hablo / *tú* → hablas | parler: *je* → parle / *tu* → parles | Agreement-sensitive output | Shifts inflection preference | BLOOM, Gemma, Llama, Mistral, Qwen; model-specific heatmaps |
| 215 | C/F · First versus third person singular; variant | work: *I* → work / *she* → works | hablar: *yo* → hablo / *ella* → habla | Agreement-sensitive output | Shifts inflection preference | Same model families; no single shared layer index |
| 216 | C/F · First versus third person plural; variant | hablar: *nosotros* → hablamos / *ellos* → hablan | parler: *nous* → parlons / *ils* → parlent | Agreement-sensitive output | Shifts inflection preference | Same model families; model-specific head sets |
| 217 | C/F · Third-person number contrast; variant | walk: *she* → walks / *they* → walk | hablar: *ella* → habla / *ellas* → hablan | Agreement-sensitive output | Shifts inflection preference | Same model families; model-specific head sets |

### Detection and refusal are different head roles

[Detection-to-refusal study][RF], §3–4 (preprint). Set interventions support a pathway; individual-head semantics remain incomplete and effects vary by architecture. Italics in the second row mark cues rather than attention targets.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 218 | R/C · Harm-sensitive token selection | Help me *steal* an account⟦.⟧ | Help me *forge* a certificate⟦.⟧ | Harm-sensitive output; exact code unknown | Can increase downstream refusal contribution | Llama, Mistral, Guanaco, Qwen instruction models; early/middle sets |
| 219 | C/F · Refusal-direction writer | Request to *steal an account* … | Request to *forge a certificate* … | Refusal-aligned residual contribution | Promotes refusal-style responses | Same families; later sets |

### Spatial induction and conditional distributions

[Spatial Induction Heads][CA], §4 and Appendix H (preprint). The rows describe mathematical constructions motivated by task-trained models, not four located natural-language heads. Layers use the paper's one-based numbering. Smoothing is a variant of the matching head.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 220 | T · Dedicated offset gather | Grid t−1: *left neighbor* → ⟦cell t⟧ | Grid t−1: *upper neighbor* → ⟦cell t⟧ | One routed cell state | Builds neighborhood representation | Constructed two-layer model; Layer 1 |
| 221 | T · Shared neighborhood gather | Grid t−1: *left, center, right* → ⟦cell t⟧ | Grid t−1: *north, center, south* → ⟦cell t⟧ | Combined encoded states | MLP separates offset slots | Alternative construction; Layer 1 |
| 222 | T · Matching-neighborhood outcome aggregator | Earlier pattern 010 → *1* … ⟦pattern 010⟧ | Earlier pattern 111 → *0* … ⟦pattern 111⟧ | Normalized outcome counts | Predicts conditional distribution | Matching head; Layer 2 |
| 223 | T · Prior-smoothed spatial matcher; variant | Pattern 010: *outcomes 1,1,0* plus *prior* | Pattern 111: *outcomes 0,1* plus *prior* | Smoothed outcome frequencies | Avoids zero probabilities in constructed readout | Matching head plus auxiliary token; Layer 2 |

### Value transforms can compensate for imperfect attention

[Visual training-dynamics study][VM], §3. These are different solutions to sparse modular addition in a simplified one-layer model. Only the initial prefix matters; the suffix is distractor data. Examples use five relevant positions and a learned pooling query.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 224 | T · Position-selected prefix pooling; idealized | *1 0 1 0 1* ; 0 1 … | *0 1 0 1 0* ; 1 1 … | Prefix composition | MLP maps pooled state to modular sum | One-layer toy model; pooling attention |
| 225 | T/R · Distractor attention canceled by values | 1 0 1 0 1 ; *distractor 0* | 0 1 0 1 0 ; *distractor 1* | Collapsed distractor values | Preserves suffix invariance despite attention | Same toy architecture; learned solution |
| 226 | T/R · Nonzero-prefix selection | *1* 0 *1* 0 *1* ; distractors | 0 *1* 0 *1* 0 ; distractors | Selective prefix summary | Still supports prefix-sum decoding | Same toy architecture; learned variant |
| 227 | T/R · Partial positional invariance | 1 0 1 0 1 ; *sixth token 0* | 1 0 1 0 1 ; *sixth token 1* | Summary retains nuisance variation | MLP needs additional decision regions | Same toy architecture; learned variant |

### Retrieval versus streaming context

[DuoAttention][DU], Figure 1 and §2.1. The two named heads illustrate the broader distinction. Compression effects were evaluated for head sets, not proof of a complete algorithm for either individual head.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 228 | R/C · Distant relevant-context reader; instance | Favorite gem: *opal*. … Which gem⟦?⟧ | Secret word: *cedar*. … Which word⟦?⟧ | Unknown beyond retrieved information | Retrieval-set cache restriction harms recall | Llama-2-7B-32K-Instruct L15H12 |
| 229 | R/C · Sink-and-recent reader; instance | *BOS* … *opened the* ⟦gate⟧ | *BOS* … *lifted a* ⟦cup⟧ | Unknown | Streaming-set middle-cache removal has small tested effect | Same model L10H1 |

### Object-related information across vision layers

[Object-DINO][OD], §3–5. These are similarity-feature associations in Q/K/V, not literal attention maps or per-head causal segmenters. Italics mark image regions. The measured downstream improvement uses an external selection/localization pipeline.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 230 | F · Intermediate object-centric heads | Image: *bicycle foreground* against wall | Image: *dog foreground* against grass | Object-related patch similarities | Selected features improve external localization | DINO; selected heads in L8–10 |
| 231 | F · Late object-centric heads; layer variant | Image: *boat foreground* against water | Image: *bird foreground* against sky | Object-related patch similarities | Selecting useful heads improves external localization | DINO L11; other final-layer heads can be noisy |

### Local and global visual attention

[Self-supervised ViT comparison][VC], §2 and Appendix E. Patterns are aggregated across trained heads; global versus local routing does not specify individual value content. Image examples are schematic.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 232 | R · Long-range global pooling | ⟦wheel patch⟧ → *whole vehicle* | ⟦wing patch⟧ → *whole bird* | Unknown per head | Associated with image-level separability | MoCo ViT-B; later layers |
| 233 | R · Local patch reader | ⟦brick patch⟧ → *neighboring bricks* | ⟦fur patch⟧ → *nearby fur* | Unknown per head | Associated with diverse local representations | SimMIM ViT-B; distributed layers |
| 234 | R · Query-dependent local outlier | ⟦eye patch⟧ → *nearby face* | ⟦leaf patch⟧ → *nearby branch* | Unknown | Unknown individual causal effect | MoCo ViT-B; third attention layer, outlier heads |

### Cache profiling reveals mixed structural preferences

[FastGen][FG], §4. These are observed access patterns in LLaMA-65B. Cache-policy suitability is an engineering consequence; it does not decode what the head writes.

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 235 | R · Local-plus-punctuation preference | Rain fell *.* *Mira* ⟦waited⟧ | Items *:* *rope* ⟦and⟧ | Unknown | Suited to mixed retention policy | LLaMA-65B L23H0 |
| 236 | R · Broad residual context access | *Earlier details* … other notes … ⟦answer⟧ | *Opening passage* … later text … ⟦continue⟧ | Unknown | Observed profile favors full cache | LLaMA-65B L23H3 |

## Expansion: 100 further entries (237–336)

Added 2026-11-04 from **11 additional primary sources**. This batch combines behavior families, reported head instances, and explicitly labeled training regimes or partners. Repeated labels with different model coordinates are instances of the same reported role, not newly discovered algorithms. All examples are illustrations; the evidence labels above continue to apply.

### Syntax under semantic-plausibility probes

Table 1 reports zero-based indices. These are dependency readers tested under plausibility manipulations; some overlap earlier BERT entries under different indexing. Attention specialization does not establish an OV mechanism. Plausibility sensitivity varies by head and analysis. BERT can read future tokens. [SC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 237 | R · Object → verb | Mira *gave* the dog a ⟦bone⟧ | Mira *gave* the bone a ⟦dog⟧ | Unknown | Unknown | BERT L7H9 |
| 238 | R · Verb → adverb | The clock *quietly* ⟦ticked⟧ | The clock *angrily* ⟦ticked⟧ | Unknown | Unknown | BERT L7H3 |
| 239 | R · Subject → verb | The ⟦baker⟧ beside the oven *smiled* | The ⟦oven⟧ beside the baker *smiled* | Unknown | Unknown | BERT L7H1 |
| 240 | R · Passive verb → subject | The *bread* near the oven was ⟦baked⟧ | The *oven* near the bread was ⟦baked⟧ | Unknown | Unknown | BERT L4H10 |
| 241 | R · Preposition → object | It was the *pond* that ducks swam ⟦in⟧ | It was the *idea* that ducks swam ⟦in⟧ | Unknown | Unknown | BERT L7H10 |
| 242 | R · Recipient → verb | Mira *gave* the ⟦child⟧ a toy | Mira *gave* the ⟦toy⟧ a child | Unknown | Unknown | BERT L6H9 |
| 243 | R · Object → verb | The dog *buried* the ⟦bone⟧ | The bone *buried* the ⟦dog⟧ | Unknown | Unknown | GPT-2 L2H8 |
| 244 | R · Adverb → verb; same head | The clock *ticked* ⟦quietly⟧ | The clock *ticked* ⟦angrily⟧ | Unknown | Unknown | GPT-2 L2H8 |
| 245 | R · Verb → subject | The *baker* beside the oven ⟦smiled⟧ | The *oven* beside the baker ⟦smiled⟧ | Unknown | Unknown | GPT-2 L4H3 |
| 246 | R · Passive verb → subject; same head | The *bread* was ⟦baked⟧ | The *oven* was ⟦baked⟧ | Unknown | Unknown | GPT-2 L4H3 |
| 247 | R · Object → preposition | The ducks swam *in* the ⟦pond⟧ | The ducks swam *in* the ⟦idea⟧ | Unknown | Unknown | GPT-2 L2H0 |
| 248 | R · Object → verb | The fox *chased* the ⟦rabbit⟧ | The rabbit *chased* the ⟦fox⟧ | Unknown | Unknown | Llama-2-7B L4H11 |
| 249 | R · Verb → subject | The *child* beside the bucket ⟦laughed⟧ | The *bucket* beside the child ⟦laughed⟧ | Unknown | Unknown | Llama-2-7B L3H22 |
| 250 | R · Passive verb → subject | The *letter* was ⟦mailed⟧ | The *mountain* was ⟦mailed⟧ | Unknown | Unknown | Llama-2-7B L4H30 |
| 251 | R · Object → preposition | She poured juice *into* the ⟦glass⟧ | She poured juice *into* the ⟦rumor⟧ | Unknown | Unknown | Llama-2-7B L10H17 |

### Subject selection inside embedded clauses

These zero-based head identities come from §7. Subject-directed attention survived argument manipulations, but did not establish successful semantic integration. RoBERTa is bidirectional. [PC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 252 | R · Embedded subject reader | The ranger knew which visitor the *guide* ⟦helped⟧ | The teacher recalled which pupil the *nurse* ⟦examined⟧ | Unknown | Unknown | GPT-2-small L2H9 |
| 253 | R · Embedded subject reader; replication | The cook knew which guest the *waiter* ⟦served⟧ | The editor recalled which author the *critic* ⟦praised⟧ | Unknown | Unknown | RoBERTa-large L12H15 |

### Tentative functions in a verb-conjugation circuit

Table 4 gives these zero-based identities. Classification used very few examples, with the verb already visible. Later anchors may instead prefer initial tokens or names. The invariant category combines self/diffuse patterns without assigning each subtype; its italics indicate cues only. Circuit selection does not validate these individual functional labels. [VJ]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 254 | R · Subject anchor; tentative | *Nia* ⟦walks⟧ | *Omar* and Tess ⟦walk⟧ | Unknown | Unknown | GPT-2-small L2H1 |
| 255 | R · Subject anchor; tentative | *Nia* ⟦walks⟧ | *Omar* and Tess ⟦walk⟧ | Unknown | Unknown | GPT-2-small L2H6 |
| 256 | R · Subject anchor; tentative | *Nia* ⟦walks⟧ | *Omar* and Tess ⟦walk⟧ | Unknown | Unknown | GPT-2-small L9H4 |
| 257 | R · Subject anchor; tentative | *Nia* ⟦walks⟧ | *Omar* and Tess ⟦walk⟧ | Unknown | Unknown | GPT-2-small L10H0 |
| 258 | R · Subject anchor; tentative | *Nia* ⟦walks⟧ | *Omar* and Tess ⟦walk⟧ | Unknown | Unknown | GPT-2-small L11H4 |
| 259 | R · Subject anchor; tentative | *Nia* ⟦walks⟧ | *Omar* and Tess ⟦walk⟧ | Unknown | Unknown | GPT-2-small L11H6 |
| 260 | R · Subject anchor; tentative | *Nia* ⟦walks⟧ | *Omar* and Tess ⟦walk⟧ | Unknown | Unknown | GPT-2-small L11H7 |
| 261 | R · Diffuse subject scanner | *Nia and Omar* ⟦walk⟧ | *Tess and Ravi* ⟦run⟧ | Unknown | Unknown | GPT-2-small L0H8 |
| 262 | R · Diffuse subject scanner | *Nia and Omar* ⟦walk⟧ | *Tess and Ravi* ⟦run⟧ | Unknown | Unknown | GPT-2-small L1H0 |
| 263 | R · Conjunction reader | Nia *and* Omar ⟦walk⟧ | Tess *and* Ravi ⟦run⟧ | Unknown | Unknown | GPT-2-small L1H1 |
| 264 | R · Invariant pattern | *Nia walks* | *Omar and Tess walk* | Unknown | Unknown | GPT-2-small L0H4 |
| 265 | R · Invariant pattern | *Nia walks* | *Omar and Tess walk* | Unknown | Unknown | GPT-2-small L6H0 |

### Subject lookup versus inflection preference during tuning

GPT-2 Small, zero-based indices; Appendix C.4. Tuning deliberately teaches disagreement. Routing can persist while output preferences reverse. Attribute/collaborator examples mark cues, not measured source positions. Collaborator interventions concern downstream attention, not decoded payloads; effects depend on prompt layout. [CU]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 266 | R · End/self reader | The *⟦girls⟧* → are | *⟦He⟧* → is | Unknown | Unknown | GPT-2 L0H1 |
| 267 | R · End/self reader | The *⟦girls⟧* → are | *⟦He⟧* → is | Unknown | Unknown | GPT-2 L0H3 |
| 268 | R · End/self reader | The *⟦girls⟧* → are | *⟦He⟧* → is | Unknown | Unknown | GPT-2 L0H5 |
| 269 | R/F · Subject reader; bias flips | The *girl* carrying two ⟦baskets⟧ → is | The *boys* near the ⟦river⟧ → are | Inflection bias | Reverses after tuning | GPT-2 L8H5 |
| 270 | R · Distant subject reader | The *girl* carrying two ⟦baskets⟧ → is | The *boys* near the ⟦river⟧ → are | Unknown | Unknown | GPT-2 L10H5 |
| 271 | R/F · Subject reader; bias flips | The *girl* carrying two ⟦baskets⟧ → is | The *boys* near the ⟦river⟧ → are | Inflection bias | Reverses after tuning | GPT-2 L10H9 |
| 272 | R · Distant subject reader | The *girl* carrying two ⟦baskets⟧ → is | The *boys* near the ⟦river⟧ → are | Unknown | Unknown | GPT-2 L11H8 |
| 273 | F · Attribute writer | The *girl* near the baskets … | The *boys* beside the river … | Inflection bias | Reverses after tuning | GPT-2 L6H0 |
| 274 | F/C · Attribute writer / collaborator | The *girl* near the baskets … | The *boys* beside the river … | Inflection bias | Flips; modulates L8H5/L10H9 | GPT-2 L6H5 |
| 275 | C · Collaborator (end subject) | The *girl* … → is | The *boys* … → are | Unknown | Modulates L8H5/L10H9 | GPT-2 L1H2 |
| 276 | C · Collaborator (both layouts) | The *girl* … → is | The *boys* … → are | Unknown | Modulates L8H5/L10H9 | GPT-2 L2H11 |
| 277 | C · Collaborator (distant subject) | The *girl* … → is | The *boys* … → are | Unknown | Modulates L8H5 | GPT-2 L7H4 |
| 278 | C · Collaborator (mixed) | The *girl* … → is | The *boys* … → are | Unknown | Modulates L8H5/L10H9 | GPT-2 L1H3 |
| 279 | C · Collaborator (mixed) | The *girl* … → is | The *boys* … → are | Unknown | Modulates L8H5/L10H9 | GPT-2 L0H8 |
| 280 | C · Collaborator (mixed) | The *girl* … → is | The *boys* … → are | Unknown | Modulates L8H5 | GPT-2 L2H10 |
| 281 | C · Collaborator (mixed) | The *girl* … → is | The *boys* … → are | Unknown | Modulates L10H9 | GPT-2 L1H4 |
| 282 | C · Collaborator (mixed) | The *girl* … → is | The *boys* … → are | Unknown | Modulates L10H9 | GPT-2 L1H6 |
| 283 | C · Collaborator (mixed) | The *girl* … → is | The *boys* … → are | Unknown | Modulates L10H9 | GPT-2 L0H9 |

### Chess move-history patterns

LCB uses source/destination tokens for alternating players. Indices here are **one-based**. Examples use schematic selection phases, not literal input tokens or legal game traces. These are averaged attention patterns, not recovered chess algorithms. Amorphous-row italics denote cues only. Family rows lack individual head IDs. [CH]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 284 | R · Checkers: same-phase history | *earlier source squares* … ⟦source selection⟧ | *earlier destination squares* … ⟦destination selection⟧ | Unknown | Unknown | LCB L2–4 family |
| 285 | R · Big Checkers: own moves | *White move history* … ⟦White selection⟧ | *Black move history* … ⟦Black selection⟧ | Unknown | Unknown | LCB L2–7/L9–10 family |
| 286 | R · Big Checkers: opponent moves | *Black move history* … ⟦White selection⟧ | *White move history* … ⟦Black selection⟧ | Unknown | Unknown | LCB same family; offset variant |
| 287 | R · Window Pane: conditional phase | *White destinations* … ⟦White destination selection⟧ | *all earlier squares* … ⟦other phase⟧ | Unknown | Unknown | LCB L3–7/L9 family |
| 288 | R · Columns: fixed phase | *earlier source phase* … ⟦any selection⟧ | *earlier destination phase* … ⟦any selection⟧ | Unknown | Unknown | LCB L1–5 family |
| 289 | R · Waffle: immediate source | White source *e2* … ⟦White destination selection⟧ | Black source *g8* … ⟦Black destination selection⟧ | Unknown | Unknown | LCB L3H5; destination phase |
| 290 | R · Waffle: both destination histories | *White/Black destinations* … ⟦White source selection⟧ | *White/Black destinations* … ⟦Black source selection⟧ | Unknown | Unknown | LCB L3H5; source phase |
| 291 | R · Backslash: four tokens back | *own preceding source* … ⟦source phase⟧ | *own preceding destination* … ⟦destination phase⟧ | Unknown | Unknown | LCB L1H5 |
| 292 | R · Backslash; second instance | *White same phase four tokens earlier* … ⟦White phase⟧ | *Black same phase four tokens earlier* … ⟦Black phase⟧ | Unknown | Unknown | LCB L1H12 |
| 293 | R · Amorphous averaged attention | *varied early-game move histories* | *varied mid-game move histories* | Unknown | Unknown | LCB L12H1–H3 family |
| 294 | R · Big Checkers + Backslash | *move history / four-token offset* … ⟦source phase⟧ | *move history / four-token offset* … ⟦destination phase⟧ | Unknown | Unknown | LCB L4H12 |

### Sorting: specialization and distribution calibration

One-layer task-trained transformers; these are developmental regimes, not five simultaneously distinct heads. Region boundaries depend on training. The suppressor operates in parallel with the copying head, so it cannot inspect that head's current output. Dormant-row italics indicate task cues, not active routing. [LS]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 295 | T/R · Nearest-greater copier | 17 *9* 4 ; ⟦4⟧ → 9 | 22 6 *12* ; ⟦6⟧ → 12 | Token identity | Promotes next sorted item | One-layer sorting model |
| 296 | T/R · Regional copier | 41 *13* 7 ; ⟦7⟧ → 13 | 48 33 *39* ; ⟦33⟧ → 39 | Region-limited copying | Shares vocabulary across heads | Two-head vocabulary-splitting regime |
| 297 | T/R · Overlapping copiers | 19 *11* 5 ; ⟦5⟧ → 11 | 30 8 *16* ; ⟦8⟧ → 16 | Overlapping copy evidence | Joint sorting contributions | Intermediate training regime |
| 298 | T/C · Parallel copy suppressor | 18 *10* 3 ; ⟦3⟧ → 10 | 26 9 *14* ; ⟦9⟧ → 14 | Negative copy contribution | Sharpens final distribution | Two-head small-spacing regime |
| 299 | T/R · Nearly dormant partner | Sort *18 10 3* | Sort *26 9 14* | Negligible contribution | Other head dominates | Low-spacing-variance regime |

### Head-pattern scores in a latent-attention model

Table 3 reports these zero-based instances in a custom 114M model, evaluated on 50 TinyStories passages. Parentheses give pattern scores. These scores do not establish token-copying OV transforms or causal induction circuits. [ML]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 300 | R · Induction pattern (.250) | amber *key* … ⟦amber⟧ | silver *bell* … ⟦silver⟧ | Unknown | Unknown | 114M MLA L12H6 |
| 301 | R · Induction pattern (.240) | amber *key* … ⟦amber⟧ | silver *bell* … ⟦silver⟧ | Unknown | Unknown | 114M MLA L12H5 |
| 302 | R · Induction pattern (.204) | amber *key* … ⟦amber⟧ | silver *bell* … ⟦silver⟧ | Unknown | Unknown | 114M MLA L12H7 |
| 303 | R · Induction pattern (.202) | amber *key* … ⟦amber⟧ | silver *bell* … ⟦silver⟧ | Unknown | Unknown | 114M MLA L12H2 |
| 304 | R · Induction pattern (.194) | amber *key* … ⟦amber⟧ | silver *bell* … ⟦silver⟧ | Unknown | Unknown | 114M MLA L12H3 |
| 305 | R · Previous-token pattern (.971) | Mira *opened* ⟦the⟧ | Theo *carried* ⟦a⟧ | Unknown | Unknown | 114M MLA L3H3 |
| 306 | R · Previous-token pattern (.953) | Mira *opened* ⟦the⟧ | Theo *carried* ⟦a⟧ | Unknown | Unknown | 114M MLA L10H6 |
| 307 | R · Previous-token pattern (.948) | Mira *opened* ⟦the⟧ | Theo *carried* ⟦a⟧ | Unknown | Unknown | 114M MLA L2H2 |

### Compositional execution through positional pointers

Small task-trained encoder–decoder; zero-based indices. Enc-self means encoder self-attention; Dec-cross means decoder-to-encoder attention. Examples abbreviate complete episodes and symbol/color bindings. Partner rows are reported similar-function instances, with weaker individual characterization than the principal circuit. [CP]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 308 | T/C · Question broadcast | Question *A* F B; support ⟦A⟧=green | Question C F *D*; support ⟦D⟧=yellow | Question index | Addresses output keys | Enc-self L0H5 |
| 309 | T/C · Primitive pairing | Support: *A*=⟦green⟧ | Support: *D*=⟦yellow⟧ | Question index | Addresses output keys | Enc-self L1H1 |
| 310 | T/C · Primitive retrieval | Support: A F *B*=⟦blue⟧ green blue; B=blue | Support: *C* G D=⟦yellow⟧ yellow; C=yellow | Primitive position | Feeds scanner | Enc-self L1H0 |
| 311 | T/C · Function retrieval | Support: A *F* B=⟦blue⟧ green blue | Support: C *G* D=⟦yellow⟧ yellow | Function position | Feeds scanner | Enc-self L1H2 |
| 312 | T/C · RHS scanner | Support: A F B=*blue* green blue; decoder ⟦SOS⟧ | Support: C G D=yellow *yellow*; decoder SOS ⟦yellow⟧ | Relative argument index | Addresses output query | Dec-cross L0H6 |
| 313 | T/C · Output copier | Support: A=*green*; decoder ⟦current position⟧ → green | Support: D=*yellow*; decoder ⟦current position⟧ → yellow | Token identity | Promotes selected token | Dec-cross L1H5 |
| 314 | T/R · Broadcast partner | Question *B* F A; support ⟦B⟧=blue | Question *D* G C; support ⟦D⟧=yellow | Question index | Parallel key pathway | Enc-self L0H7 |
| 315 | T/R · Retrieval partner | Support: A F *B*=⟦blue⟧ green blue | Support: *C* G D=⟦yellow⟧ yellow | Primitive position | Parallel scanner input | Enc-self L1H4 |
| 316 | T/R · Scanner partner | Support: A F B=*blue* green blue; decoder ⟦SOS⟧ | Support: C G D=yellow *yellow*; decoder SOS ⟦yellow⟧ | Relative argument index | Parallel query pathway | Dec-cross L0H0 |
| 317 | T/R · Scanner partner | Support: A F B=blue *green* blue; decoder SOS ⟦blue⟧ | Support: C G D=*yellow* yellow; decoder ⟦SOS⟧ | Relative argument index | Parallel query pathway | Dec-cross L0H3 |
| 318 | T/R · Output partner | Support: A=*green*; decoder ⟦later position⟧ → green | Support: D=*yellow*; decoder ⟦later position⟧ → yellow | Token identity | Partial output compensation | Dec-cross L1H1 |
| 319 | T/R · Output partner | Support: B=*blue*; decoder ⟦later position⟧ → blue | Support: C=*yellow*; decoder ⟦later position⟧ → yellow | Token identity | Partial output compensation | Dec-cross L1H3 |

### Arithmetic operands and operator travel separately

Llama-3-8B, zero-based indices. Appendix B.2 and Figure 14 isolate three shared arithmetic heads. Their transported inputs feed subsequent MLP processing; these heads are not themselves complete arithmetic algorithms. [AH]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 320 | C · Operator reader | 28 *+* 13 ⟦=⟧ | 84 *−* 27 ⟦=⟧ | Operator representation | Supplies calculation context | Llama-3-8B L2H2 |
| 321 | C · Second-operand reader | 28 + *13* ⟦=⟧ | 84 − *27* ⟦=⟧ | Second operand | Supplies calculation context | Llama-3-8B L15H13 |
| 322 | C · First-operand reader | *28* + 13 ⟦=⟧ | *84* − 27 ⟦=⟧ | First operand | Supplies calculation context | Llama-3-8B L16H21 |

### Arithmetic heads identified through intervention

Tables 1–2 and Appendix C identify these zero-indexed components. **Attention destinations are unresolved here:** italics mark task cues. C denotes ablation evidence, not a recovered algorithm. Importance differs by operation; multiplication effects are comparatively modest. [AN]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 323 | C/F · Addition/subtraction contributor | *4 + 7* = | *16 − 9* = | Prediction-related signal | Activates answer-related FFNs | Llama-7B L17H22 |
| 324 | C/F · Division contributor | *63 ÷ 9* = | *48 ÷ 6* = | Prediction-related signal | Activates answer-related FFNs | Llama-7B L14H19 |
| 325 | C/F · Mixed arithmetic contributor | *81 ÷ 9* = | *32 − 17* = | Unknown | Ablation lowers accuracy | Llama-7B L15H9 |
| 326 | C/F · Mixed arithmetic contributor | *29 + 14* = | *74 − 38* = | Unknown | Ablation lowers accuracy | Llama-7B L15H23 |
| 327 | C/F · Subtraction-sensitive contributor | *52 − 19* = | *91 − 46* = | Unknown | Ablation harms subtraction | Llama-7B L16H1 |
| 328 | C/F · Multiplication-sensitive contributor | *7 × 8* = | *13 × 12* = | Unknown | Modest multiplication effect | Llama-7B L20H18 |
| 329 | C/F · Mixed arithmetic contributor | *12 × 13* = | *72 ÷ 8* = | Unknown | Ablation lowers accuracy | GPT-J L7H0 |
| 330 | C/F · Subtraction contributor | *42 − 18* = | *65 − 29* = | Prediction-related signal | Supports subtraction FFNs | GPT-J L13H9 |
| 331 | C/F · Multiplication-sensitive contributor | *14 × 12* = | *16 × 13* = | Unknown | Ablation harms multiplication | GPT-J L0H11 |
| 332 | C/F · Mixed arithmetic contributor | *11 × 17* = | *96 ÷ 12* = | Unknown | Ablation lowers accuracy | GPT-J L15H6 |
| 333 | C/F · Division-sensitive contributor | *84 ÷ 12* = | *99 ÷ 11* = | Unknown | Ablation harms division | GPT-J L14H14 |

### Pronouns: bound-reference versus recent-token routes

§6 studies instruction-tuned models. These are head-set roles, not single identified algorithms. Italics show diagnostic cues rather than established attention destinations. The proposed payload interpretation is broader than the patching evidence; residual-subspace results are not assigned to individual heads. [PF]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 334 | C/F · Bound-reference copying | The *pilot said she* was ready. The baker said he was tired. The pilot said that … | The *cook said he* would help. The artist said she was leaving. The cook said that … | Occupation/pronoun binding; inferred | Targeted set ablation harms reference copying | OLMo-2-0425-1B-Instruct; selected 11-head set |
| 335 | C/F · Recent-pronoun copying | The pilot said she was ready. The baker said *he* was tired. The pilot said that … | The cook said he would help. The artist said *she* was leaving. The cook said that … | Recent pronoun; inferred | Distributed influence on recency-based copying | OLMo-2-0425-1B-Instruct; distributed set |
| 336 | C/F · Bound-reference copying; replication | The *sailor said she* knew the way. The guide said he was lost. The sailor said that … | The *nurse said he* had arrived. The driver said she was waiting. The nurse said that … | Occupation/pronoun binding; inferred | Targeted set ablation harms reference copying | Qwen2.5-7B-Instruct; selected 29-head set |

## Expansion: 100 additional entries (337–436)

Added 2026-11-05 from five further primary sources. These include individual head observations, context-dependent output associations, and explicitly labeled unlocalized families; they are not 100 newly established algorithms.

### Logical clauses, truth values, and mixed routing

Zero-based Qwen3 identities from Figures 7, 13–14 of the preprint. These rows report attention patterns; circuit-level causal results do not establish each head's payload. Mixed-role examples are schematic. A first-token sink is not thereby proven useless. [LG]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 337 | R · Clause delimiters | P is True *,* Q is False ⟦,⟧ | X is False *,* Y is True ⟦,⟧ | Unknown | Unknown | Qwen3-8B L0H25 |
| 338 | R · Clause delimiters | P is True *,* Q is False ⟦,⟧ | X is False *,* Y is True ⟦,⟧ | Unknown | Unknown | Qwen3-8B L1H13 |
| 339 | R · Clause delimiters | P is True *,* Q is False ⟦,⟧ | X is False *,* Y is True ⟦,⟧ | Unknown | Unknown | Qwen3-8B L1H18 |
| 340 | R · Within-clause aggregation | *P is* ⟦True⟧, Q is False | P is True, (*P and Q*⟦)⟧ | Unknown | Unknown | Qwen3-8B L7H27 |
| 341 | R · Within-clause aggregation | *P is* ⟦True⟧, Q is False | P is True, (*P and Q*⟦)⟧ | Unknown | Unknown | Qwen3-8B L8H11 |
| 342 | R · Within-clause aggregation | *P is* ⟦True⟧, Q is False | P is True, (*P and Q*⟦)⟧ | Unknown | Unknown | Qwen3-8B L9H1 |
| 343 | R · Truth-value lookup | P is *True*, Q is *False*, (P or Q) ⟦is⟧ | X is *False*, Y is *True*, (X and Y) ⟦is⟧ | Unknown | Unknown | Qwen3-8B L26H4 |
| 344 | R · Truth-value lookup | P is *True*, Q is *False*, (P or Q) ⟦is⟧ | X is *False*, Y is *True*, (X and Y) ⟦is⟧ | Unknown | Unknown | Qwen3-8B L27H19 |
| 345 | R · Truth-value lookup | P is *True*, Q is *False*, (P or Q) ⟦is⟧ | X is *False*, Y is *True*, (X and Y) ⟦is⟧ | Unknown | Unknown | Qwen3-8B L31H31 |
| 346 | R · Initial-position sink | *.* P is True, (P) ⟦is⟧ | *P* is False, (not P) ⟦is⟧ | Unknown | Unknown | Qwen3-8B L7H4 |
| 347 | R · Local logical binding | *P is* ⟦True⟧ | (*not* ⟦Q⟧) | Unknown | Unknown | Qwen3-8B L0H1 |
| 348 | R · Local logical binding | *P is* ⟦True⟧ | (*not* ⟦Q⟧) | Unknown | Unknown | Qwen3-8B L0H24 |
| 349 | R · Self-position processing | P is *⟦True⟧* | (P *⟦and⟧* Q) | Unknown | Unknown | Qwen3-8B L12H20 |
| 350 | R · Self-position processing | P is *⟦True⟧* | (P *⟦and⟧* Q) | Unknown | Unknown | Qwen3-8B L22H12 |
| 351 | R · Expression-region reader | P is True, Q is False, *(P or Q)* ⟦is⟧ | X is False, Y is True, *(X and Y)* ⟦is⟧ | Unknown | Unknown | Qwen3-8B L18H2 |
| 352 | R · Expression + initial position | *P* is True, Q is False, *(P or Q)* ⟦is⟧ | *X* is False, Y is True, *(X and Y)* ⟦is⟧ | Unknown | Unknown | Qwen3-8B L19H31 |
| 353 | R · Expression-region reader | P is True, Q is False, *(P or Q)* ⟦is⟧ | X is False, Y is True, *(X and Y)* ⟦is⟧ | Unknown | Unknown | Qwen3-8B L21H13 |
| 354 | R · Boundary/binding mixture | *P is True* ⟦,⟧ Q is False | P is True, *Q is* ⟦False⟧ | Unknown | Unknown | Qwen3-8B L0H19 |
| 355 | R · Self/binding mixture | *P is* *⟦True⟧* | *Q is* *⟦False⟧* | Unknown | Unknown | Qwen3-8B L0H31 |
| 356 | R · Self/selective mixture | *P* is True, (P) *⟦is⟧* | *Q* is False, (not Q) *⟦is⟧* | Unknown | Unknown | Qwen3-8B L1H22 |

### Context-sensitive head contributions to MLP neurons

Table 2 and Appendix F provide these automatically proposed explanations. Italics mark cues, not attention destinations; arrows name the associated token, not guaranteed completions. The feature column names a neuron's preferred token. `flat` preserves the paper's head ID; `Nlayer.neuron` identifies its MLP target, **not the head's layer**. GPT-2 S/M/L mean Small/Medium/Large. [LK]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 357 | F · Restriction | For *training purposes* → only | For *authorized operators* → only | only | Unknown | GPT-2-L:flat538;N31.3621 |
| 358 | F · Evidence summary | The findings agree. *Taken* → together | Both trials support it. *Taken* → together | together | Unknown | GPT-2-L:flat123;N31.4378 |
| 359 | F · Ranking | Her song *peaked at* → number | The team *was ranked* → number | number | Unknown | GPT-2-L:flat519;N31.364 |
| 360 | F · Identifier | Enter the shipment's *tracking* → number | Write down your *reservation* → number | number | Unknown | GPT-2-L:flat548;N31.364 |
| 361 | F · Future possibility | We dream that *one* → day | Perhaps the bridge will reopen *one* → day | day | Unknown | GPT-2-M:flat225;N20.2312 |
| 362 | F · Contemporary period | The fortress stood in *present-* → day | This is its *modern-* → day | day | Unknown | GPT-2-M:flat66;N20.2312 |
| 363 | F · Correct direction | The sign pointed us *in the* → right | Their advice put us *on the* → right | right | Unknown | GPT-2-M:flat228;N21.2629 |
| 364 | F · Beneficial outcome | Her patient training finally *paid* → off | They would be *better* → off | off | Unknown | GPT-2-M:flat20;N21.1031 |
| 365 | F · No alternative | We had *no choice* → but | There was *no option* → but | but | Unknown | GPT-2-M:flat36;N21.3049 |
| 366 | F · Unspecified duration | I waited for *quite* → some | That repair took *quite* → some | some | Unknown | GPT-2-M:flat59;N23.2257 |
| 367 | F · Approximation | It weighs ten kilos *or* → so | We stayed a fortnight *or* → so | so | Unknown | GPT-2-S:flat11;N10.2003 |
| 368 | F · Shell conditional | *if test -f report;* → then | *if test -d archive;* → then | then | Unknown | GPT-2-S:flat109;N10.1453 |
| 369 | F · Current repetition | She tried again, *this* → time | He returned, *this* → time | time | Unknown | GPT-2-S:flat115;N11.822 |
| 370 | F · Open-ended list | Rope, candles, blankets, *and so* → on | Apples, pears, plums, *and so* → on | on | Unknown | GPT-2-S:flat10;N11.3015 |
| 371 | F · Knowledge gap | Very *little is known* → about | Almost *nothing is known* → about | about | Unknown | Pythia-160M:flat0;N9.602 |
| 372 | F · List aggregation | *Ravi, Mina, and Theo,* → all | *The lamps, windows, and doors,* → all | all | Unknown | Pythia-160M:flat71;N9.2251 |
| 373 | F · List extension | Paints, brushes, clay, *and much* → more | Maps, books, charts, *and much* → more | more | Unknown | Pythia-160M:flat80;N10.2509 |
| 374 | F · Open-ended list | Cups, plates, bowls, *and so* → on | Red, blue, green, *and so* → on | on | Unknown | Pythia-160M:flat10;N10.2734 |
| 375 | F · Legal/code alternative | *Unless required by local law* → or | *open_file(path)* → or | or | Unknown | Pythia-1.4B:flat48;N20.750 |
| 376 | F · Research purpose | *The objective of* → this | *The purpose of* → this | this | Unknown | Pythia-1.4B:flat63;N20.3507 |
| 377 | F · Vulnerability | *Their savings were* → at | *Several lives remained* → at | at | Unknown | Pythia-1.4B:flat290;N21.3152 |
| 378 | F · Example introduction | Choose *summer fruits* → like | Try *quiet activities* → like | like | Unknown | Pythia-1.4B:flat273;N23.7671 |

### Lexical associations in value/output weight projections

Appendix C.1 reports static OV projections, **not attention routes**. Italics mark cues. Labels summarize subsets of noisy mappings, not complete functions. “Association” means vocabulary-space alignment. S/M/L identify GPT-2 sizes; indices follow the source. [ES]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 379 | F · Name fragments | The register listed *Harr…* | Her surname began *McD…* | Association | Unknown | GPT-2-M L21H7 |
| 380 | F · Initial/word-part links | The initial *B* beside a name | A surname ending in *…ington* | Association | Unknown | GPT-2-M L19H13 |
| 381 | F · Prepositional collocations | She spoke *on* our behalf | Stay *within* the boundary | Association | Unknown | GPT-2-M L20H9 |
| 382 | F · Related nominal forms | Several *stories* lay unfinished | They printed two *magazines* | Association | Unknown | GPT-2-S L10H11 |
| 383 | F · Fixed phrase fragments | *With* respect to the plan | *Of* course they agreed | Association | Unknown | GPT-2-L L27H6 |
| 384 | F · Feminine lexical association | The *actress* arrived first | A *woman* signed the register | Association | Unknown | GPT-2-M L18H1 |
| 385 | F · Feminine/name association | The note referred to *her* | *She* introduced the cast | Association | Unknown | GPT-2-L L27H12 |
| 386 | F · Reflexive-pronoun association | *They* repaired it themselves | *He* prepared himself | Association | Unknown | GPT-2-S L9H7 |
| 387 | F · Geographic lexical association | A shipment from *Manitoba* | The *Saudi* delegation arrived | Association | Unknown | GPT-2-S L11H2 |
| 388 | F · Regional-place association | A journey across *India* | A route through *Scotland* | Association | Unknown | GPT-2-M L16H6 |
| 389 | F · Australian/Canadian association | News from *Australia* | Snow across *Alberta* | Association | Unknown | GPT-2-M L16H2 |
| 390 | F · Nationality/name association | An *Indonesian* newspaper | A *Vietnamese* family name | Association | Unknown | GPT-2-M L21H12 |
| 391 | F · Canadian/place association | A report from *Quebec* | A speech about *Canada* | Association | Unknown | GPT-2-L L23H5 |
| 392 | F · British spelling association | They *organise* the festival | A *colourful* illustration | Association | Unknown | GPT-2-M L19H4 |
| 393 | F · Related evaluative wording | A *peaceful* exchange | An *unexpected* arrival | Association | Unknown | GPT-2-M L13H8 |
| 394 | F · Verb-form association | She was *testifying* | The council *regulates* trade | Association | Unknown | GPT-2-M L12H14 |
| 395 | F · Error/correctness vocabulary | The form was filled *incorrectly* | He acted *properly* | Association | Unknown | GPT-2-M L14H1 |
| 396 | F · Interview/review vocabulary | An *interviewer* asked why | The *reviewers* disagreed | Association | Unknown | GPT-2-L L24H9 |
| 397 | F · Media-role vocabulary | The *editorial* appeared today | They work in *broadcasting* | Association | Unknown | GPT-2-M L14H13 |
| 398 | F · Numeral association | Ticket *58* was missing | Box *213* was sealed | Association | Unknown | GPT-2-M L0H9 |
| 399 | F · Legal vocabulary | The *judicial* decision arrived | It was *legally* permitted | Association | Unknown | GPT-2-M L17H6 |
| 400 | F · Institutional vocabulary | A *scholarship* was awarded | The *staff* held a meeting | Association | Unknown | GPT-2-M L17H7 |
| 401 | F · Surname/fragment association | The name *Morgan* appeared | A surname ending *…son* | Association | Unknown | GPT-2-M L22H5 |
| 402 | F · Year/news-format association | An archive dated *2016* | A *2013* news bulletin | Association | Unknown | GPT-2-M L19H12 |

### MAPS: proposed transformations from head parameters

These zero-based instances come from Table 25 and Appendix D. Labels are hypotheses from static mappings, except the name-copying case also has prompt-dependent output measurements. Italics mark inputs/cues, not attention routes. [MP]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 403 | F · Historical-period association | A biography of *Lincoln* → period-related vocabulary | A portrait of *Darwin* → period-related vocabulary | Period evidence | Unknown | Pythia-6.9B L15H3 |
| 404 | F · Protective/resistance stems | *resist…* → resistance vocabulary | *protect…* → protection vocabulary | Related lexemes | Unknown | Pythia-6.9B L16H1 |
| 405 | F · Longer time scales | *days* → weeks | *decades* → centuries | Duration association | Unknown | Pythia-6.9B L16H11 |
| 406 | F · Anatomical associations | *corneal* → eye vocabulary | *gingival* → dental vocabulary | Medical associations | Unknown | Pythia-6.9B L22H13 |
| 407 | F · Fictional-universe associations | *Hogwarts* → wizard vocabulary | *Vulcan* → space-fiction vocabulary | Related fictional terms | Unknown | GPT-2-XL L26H2 |
| 408 | F/R · Prompt-sensitive name copying | Nia→Nia; Omar→Omar; *Tess*→ | Mira→Mira; Ravi→Ravi; *Theo*→ | Name identity | Copying varies with prompt | GPT-2-S L8H11 |

### MAPS: relation-specific promotion and opposition

Tables 6–7 report these head families. Feature signs refer to static vocabulary projections; causal effects of these particular suppression families remain unknown. Italics mark relation inputs. Family rows do not assign individual layer IDs. [MP]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 409 | F · Word-final letter mapping | Last letter of *lamp* → p | Last letter of *boat* → t | Final-letter support | Unknown | Llama-3.1-70B; mapped set |
| 410 | F · Compound-word association | *rain* → rainfall | *sun* → sunlight | Compound support | Unknown | Llama-3.1-70B; mapped set |
| 411 | F · Homophone association | *knight* → night | *flour* → flower | Homophone support | Unknown | Llama-3.1-70B; two mapped heads |
| 412 | F · Comparative opposition | *small* → opposition to smaller | *bright* → opposition to brighter | Opposition | Unknown | Llama-3.1-8B; mapped set |
| 413 | F · Past-form opposition | *walk* → opposition to walked | *write* → opposition to wrote | Opposition | Unknown | Llama-3.1-8B; mapped set |
| 414 | F · Antonym opposition | *dark* → opposition to light | *early* → opposition to late | Opposition | Unknown | Llama-3.1-8B; mapped set |
| 415 | F · Superclass opposition | *sparrow* → opposition to bird | *salmon* → opposition to fish | Opposition | Unknown | Llama-3.1-70B; mapped set |

### Multilingual translation: syntax and current-versus-next alignment

Tables 5, 7, 10–11; zero-based R-finetune heads. S2S is bidirectional encoder attention, T2T causal decoder attention, T2S cross-attention. EnDe/DeEn/FrEn identify translation directions. Positional examples use English on the relevant side. “Pruned” marks subsequent removal. Attention alignment does not establish the output payload or causal function. [NN]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 416 | R · Previous token | Mira *opened* ⟦the⟧ gate | A *silver* ⟦bell⟧ rang | Unknown | Unknown | S2S L1H6 |
| 417 | R · Previous token | Theo *carried* ⟦a⟧ lantern | The *old* ⟦bridge⟧ swayed | Unknown | Unknown | S2S L2H6 |
| 418 | R · Next token | the ⟦red⟧ *boat* | a ⟦brass⟧ *bell* | Unknown | Unknown | S2S L1H7 |
| 419 | R · Previous target token | Nia *found* ⟦the⟧ key | Omar *closed* ⟦a⟧ window | Unknown | Unknown | T2T L0H5 |
| 420 | R · Noun → adjective | der *kleine* ⟦Hund⟧ | ein *altes* ⟦Haus⟧ | Unknown | Unknown | S2S L3H6; DeEn |
| 421 | R · Object → verb; pruned | Mira *opened* the ⟦gate⟧ | Theo *carried* a ⟦lantern⟧ | Unknown | Unknown | S2S L3H2; EnDe |
| 422 | R · Object → verb | Nia *mended* the ⟦sail⟧ | Omar *found* a ⟦key⟧ | Unknown | Unknown | S2S L2H0; EnDe |
| 423 | R · Verb → object | Mira ⟦opened⟧ the *gate* | Theo ⟦carried⟧ a *lantern* | Unknown | Unknown | S2S L2H2; EnDe |
| 424 | R · Verb → object | Nia ⟦mended⟧ the *sail* | Omar ⟦found⟧ a *key* | Unknown | Unknown | S2S L4H2; EnDe |
| 425 | R · Adjective → noun | un *livre* ⟦rouge⟧ | une *maison* ⟦blanche⟧ | Unknown | Unknown | S2S L5H0; FrEn |
| 426 | R · Verb → subject | *Mira* ⟦waited⟧ outside | *Theo* ⟦laughed⟧ softly | Unknown | Unknown | S2S L0H0; EnDe |
| 427 | R · Subject → verb | Le ⟦garçon⟧ *chante* | La ⟦fille⟧ *danse* | Unknown | Unknown | S2S L3H7; FrEn |
| 428 | R · Verb → adverb; pruned | Elle ⟦parle⟧ *doucement* | Il ⟦marche⟧ *lentement* | Unknown | Unknown | S2S L2H5; FrEn |
| 429 | R · Current-word alignment | source: a *dog* sleeps; target: ein ⟦Hund⟧ | source: the *house*; target: das ⟦Haus⟧ | Unknown | Unknown | T2S L0H7; EnDe |
| 430 | R · Current-word alignment | source: a *dog* sleeps; target: ein ⟦Hund⟧ | source: the *house*; target: das ⟦Haus⟧ | Unknown | Unknown | T2S L1H5; EnDe |
| 431 | R · Current-word alignment | source: a *dog* sleeps; target: ein ⟦Hund⟧ | source: the *house*; target: das ⟦Haus⟧ | Unknown | Unknown | T2S L2H5; EnDe |
| 432 | R · Current-word alignment | source: a *dog* sleeps; target: ein ⟦Hund⟧ | source: the *house*; target: das ⟦Haus⟧ | Unknown | Unknown | T2S L2H7; EnDe |
| 433 | R · Next-word alignment | source: a *dog* sleeps; target: ⟦ein⟧ → Hund | source: the *house*; target: ⟦das⟧ → Haus | Unknown | Unknown | T2S L3H7; EnDe |
| 434 | R · Next-word alignment | source: a *dog* sleeps; target: ⟦ein⟧ → Hund | source: the *house*; target: ⟦das⟧ → Haus | Unknown | Unknown | T2S L4H0; EnDe |
| 435 | R · Next-word alignment | source: a *dog* sleeps; target: ⟦ein⟧ → Hund | source: the *house*; target: ⟦das⟧ → Haus | Unknown | Unknown | T2S L4H2; EnDe |
| 436 | R · Next-word alignment | source: a *dog* sleeps; target: ⟦ein⟧ → Hund | source: the *house*; target: ⟦das⟧ → Haus | Unknown | Unknown | T2S L4H7; EnDe |


## Expansion: cross-domain and small-model evidence (437–540)

Added 2026-11-05: 104 entries from eleven further papers and one supporting author-code source. Domain-specific heads are included to broaden the inventory; protein, audio, vision, and board-model examples are not claims about language-model word generation.

### Protein attention: spatial relationships and residue preferences

Figures 1–3 and Appendix C.5; **one-based** indices. Schematic amino-acid sequences, not English. Repeated IDs indicate multiple preferences. PTM means post-translational modification. Payloads remain unresolved. [PB]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 437 | R · Spatial-contact reader | ⟦residue i⟧ … *residue j: nearby in 3D* | *residue k: nearby in 3D* … ⟦residue m⟧ | Unknown | Unknown | TapeBert L12H4 |
| 438 | R · Binding-site reader | ⟦residue i⟧ … *binding site j* | *binding site k* … ⟦residue m⟧ | Unknown | Unknown | TapeBert L7H1 |
| 439 | R · Binding-site reader | ⟦residue i⟧ … *ligand-binding residue* | *drug-binding residue* … ⟦residue m⟧ | Unknown | Unknown | TapeBert L11H6 |
| 440 | R · Modified-residue preference | ⟦residue i⟧ … *PTM site j* | *PTM site k* … ⟦residue m⟧ | Unknown | Unknown | TapeBert L11H6 |
| 441 | R · Alanine preference | ⟦residue i⟧ … *A* … | … *A* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L12H11 |
| 442 | R · Arginine preference | ⟦residue i⟧ … *R* … | … *R* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L12H8 |
| 443 | R · Asparagine preference | ⟦residue i⟧ … *N* … | … *N* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L8H2 |
| 444 | R · Aspartate preference | ⟦residue i⟧ … *D* … | … *D* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L12H6 |
| 445 | R · Cysteine preference | ⟦residue i⟧ … *C* … | … *C* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L11H6 |
| 446 | R · Glycine preference | ⟦residue i⟧ … *G* … | … *G* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L2H11 |
| 447 | R · Histidine preference | ⟦residue i⟧ … *H* … | … *H* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L9H10 |
| 448 | R · Isoleucine preference | ⟦residue i⟧ … *I* … | … *I* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L11H10 |
| 449 | R · Leucine preference | ⟦residue i⟧ … *L* … | … *L* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L2H12 |
| 450 | R · Lysine preference | ⟦residue i⟧ … *K* … | … *K* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L12H8 |
| 451 | R · Methionine preference | ⟦residue i⟧ … *M* … | … *M* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L3H10 |
| 452 | R · Proline preference | ⟦residue i⟧ … *P* … | … *P* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L1H11 |
| 453 | R · Serine preference | ⟦residue i⟧ … *S* … | … *S* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L12H7 |
| 454 | R · Tryptophan preference | ⟦residue i⟧ … *W* … | … *W* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L11H4 |
| 455 | R · Tyrosine preference | ⟦residue i⟧ … *Y* … | … *Y* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L12H3 |
| 456 | R · Valine preference | ⟦residue i⟧ … *V* … | … *V* … ⟦residue j⟧ | Unknown | Unknown | TapeBert L12H11 |

### Summarization: source-token preferences in decoder cross-attention

Tables 1–2, zero-based indices. Model1/2 are independently trained summarizers. These are corpus-level attention profiles, not exclusive token detectors or proven summary planners. Examples illustrate source categories; the query is unspecified. Ablation results caution against inferring importance from visibly specialized attention. [SU]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 457 | R · Punctuation-heavy profile | article: Rain fell *.*; ⟦summary step⟧ | article: He asked *,* then waited; ⟦summary step⟧ | Unknown | Unknown | Model1 L1H4 |
| 458 | R · Noun-heavy profile | article: The *bridge* collapsed; ⟦summary step⟧ | article: A *storm* arrived; ⟦summary step⟧ | Unknown | Unknown | Model1 L2H2 |
| 459 | R · Entity-enriched profile | article: *Mira* won the race; ⟦summary step⟧ | article: *Riverton* opened a library; ⟦summary step⟧ | Unknown | Unknown | Model1 L1H7 |
| 460 | R · Entity-enriched profile | article: *Theo* received the award; ⟦summary step⟧ | article: *Northstar Ltd* hired staff; ⟦summary step⟧ | Unknown | Unknown | Model1 L2H0 |
| 461 | R · Noun-heavy profile | article: A *ferry* docked; ⟦summary step⟧ | article: The *school* reopened; ⟦summary step⟧ | Unknown | Unknown | Model1 L2H4 |
| 462 | R · Noun-heavy profile | article: The *factory* closed; ⟦summary step⟧ | article: A *parade* began; ⟦summary step⟧ | Unknown | Unknown | Model1 L3H6 |
| 463 | R · Verb-heavy profile | article: The team *won*; ⟦summary step⟧ | article: The river *flooded*; ⟦summary step⟧ | Unknown | Unknown | Model2 L1H6 |
| 464 | R · Verb-heavy profile | article: The council *approved* it; ⟦summary step⟧ | article: The minister *resigned*; ⟦summary step⟧ | Unknown | Unknown | Model2 L1H7 |
| 465 | R · Noun-heavy profile | article: The *museum* opened; ⟦summary step⟧ | article: A *tunnel* collapsed; ⟦summary step⟧ | Unknown | Unknown | Model2 L2H6 |
| 466 | R · Entity-enriched profile | article: *Nia* led the team; ⟦summary step⟧ | article: *Eastbridge* restored the park; ⟦summary step⟧ | Unknown | Unknown | Model2 L3H2 |
| 467 | R · Entity-enriched profile | article: *Omar* announced the result; ⟦summary step⟧ | article: *Harbor Bank* opened a branch; ⟦summary step⟧ | Unknown | Unknown | Model2 L3H1 |
| 468 | R · Punctuation-heavy profile | article: The road closed *.*; ⟦summary step⟧ | article: It was late *,* he said; ⟦summary step⟧ | Unknown | Unknown | Model2 L1H0 |

### Music: information readable from individual head outputs

Figures 1–2 and Table 2. Italics describe acoustic cues, not token destinations. Probes use a head's last-step output; sorted plots do not identify head numbers. Feature families can overlap. Emotion probes peak in the paper's “27th layer”; earlier heads also carry signal. Proposed steering applications were not demonstrated. [MU]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 469 | F · Drum information | audio: *snare and kick* beneath a melody | audio: *hand drums* beneath singing | Probe-decodable | Unknown | MusicGen-large; selected heads |
| 470 | F · Bass information | audio: *electric bass line* | audio: *sustained low bass notes* | Probe-decodable | Unknown | MusicGen-large; selected heads |
| 471 | F · Guitar information | audio: *strummed guitar* with drums | audio: *picked guitar* solo | Probe-decodable | Unknown | MusicGen-large; selected heads |
| 472 | F · Piano information | audio: *piano arpeggios* | audio: *piano chords* under a voice | Probe-decodable | Unknown | MusicGen-large; selected heads |
| 473 | F · Genre information | audio: *jazz-like* ensemble | audio: *classical-style* instrumental | Probe-decodable | Unknown | MusicGen-large; selected heads |
| 474 | F · Musical-key information | audio: passage in *D major* | audio: passage in *E minor* | Probe-decodable | Unknown | MusicGen-large; sparse head subset |
| 475 | F · Arousal information | audio: *energetic* passage | audio: *subdued* passage | Probe-decodable | Unknown | MusicGen-large; emotion probes |
| 476 | F · Valence information | audio: *cheerful-sounding* passage | audio: *sad-sounding* passage | Probe-decodable | Unknown | MusicGen-large; emotion probes |

### Chess: spatial movement readers and future-move feedback

§3.2 and the authors' head lists; zero-based code indices. Twelve movement examples sample the repository's `good_*` lists across depth. Geometry is schematic; blockers and actual positions matter. Movement-head ablations test sets, not each listed head alone. In feedback examples, tₙ means the nth move's destination; diagrams are not legal move sequences. [LX] [LXC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 477 | C · Future-move feedback | ⟦t₁=e4⟧ reads *t₃=h7* | ⟦t₁=c5⟧ reads *t₃=f2* | Unknown | Supports immediate choice | Leela L12H12 |
| 478 | R · Knight geometry | ⟦e4⟧ reads *f6* | ⟦c3⟧ reads *a4* | Unknown | Set-level look-ahead role | Leela L0H17 |
| 479 | R · Knight geometry | ⟦e4⟧ reads *f6* | ⟦c3⟧ reads *a4* | Unknown | Set-level look-ahead role | Leela L4H3 |
| 480 | R · Knight geometry | ⟦e4⟧ reads *f6* | ⟦c3⟧ reads *a4* | Unknown | Set-level look-ahead role | Leela L9H5 |
| 481 | R · Knight geometry | ⟦e4⟧ reads *f6* | ⟦c3⟧ reads *a4* | Unknown | Set-level look-ahead role | Leela L14H22 |
| 482 | R · Bishop geometry | ⟦e4⟧ reads *g6* | ⟦c3⟧ reads *a5* | Unknown | Set-level look-ahead role | Leela L1H4 |
| 483 | R · Bishop geometry | ⟦e4⟧ reads *g6* | ⟦c3⟧ reads *a5* | Unknown | Set-level look-ahead role | Leela L6H20 |
| 484 | R · Bishop geometry | ⟦e4⟧ reads *g6* | ⟦c3⟧ reads *a5* | Unknown | Set-level look-ahead role | Leela L10H0 |
| 485 | R · Bishop geometry | ⟦e4⟧ reads *g6* | ⟦c3⟧ reads *a5* | Unknown | Set-level look-ahead role | Leela L14H20 |
| 486 | R · Rook geometry | ⟦e4⟧ reads *e7* | ⟦c3⟧ reads *h3* | Unknown | Set-level look-ahead role | Leela L0H15 |
| 487 | R · Rook geometry | ⟦e4⟧ reads *e7* | ⟦c3⟧ reads *h3* | Unknown | Set-level look-ahead role | Leela L5H10 |
| 488 | R · Rook geometry | ⟦e4⟧ reads *e7* | ⟦c3⟧ reads *h3* | Unknown | Set-level look-ahead role | Leela L10H23 |
| 489 | R · Rook geometry | ⟦e4⟧ reads *e7* | ⟦c3⟧ reads *h3* | Unknown | Set-level look-ahead role | Leela L14H16 |

### Chess: the same feedback pathway changes with the tactical position

§3 and Appendix D; original head labels preserved. These extend the preceding Leela analysis. Digits encode repeated moving pieces in the paper's puzzle taxonomy, not square numbers. Cue examples identify tested puzzle classes; individual attention routes remain conditional. [LY]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 490 | C · Fifth-move feedback | *11223* puzzle: ⟦t₁⟧ reads *t₅* | *11234* puzzle: ⟦t₁⟧ reads *t₅* | Unknown | Supports earlier choice | Leela L12H12; longer horizon |
| 491 | C · Non-mating feedback preference | *AABCA* puzzle: ⟦t₁⟧ reads *t₃* | *AABCD, C≠D* puzzle: ⟦t₁⟧ reads *t₃* | Unknown | Conditional choice contribution | Leela L12H17 |
| 492 | C · Repeated-piece feedback | *AABCC* puzzle: feedback to earlier move | *AABBD* puzzle: feedback to earlier move | Unknown | Weaker conditional contribution | Leela L13H3 |

### Dense retrieval: mixed relevance and gender signals

§4, Table 3; zero-based. Italics mark document substitutions, not attention routes. Patching establishes mediation; mixed gender/relevance content is inferred rather than decoded. Effects depend on task and pooling. [GR]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 493 | C/F · Upstream mediator | Matched documents: *he / she* teaches sailing | Matched documents: *father / mother* repairs boats | Unknown | Feeds later heads | DistilBERT-multi-qa L4H1 |
| 494 | C/F · Upstream mediator | Matched documents: *he / she* teaches sailing | Matched documents: *father / mother* repairs boats | Unknown | Feeds later heads | DistilBERT-multi-qa L4H5 |
| 495 | C/F · Upstream mediator | Matched documents: *he / she* teaches sailing | Matched documents: *father / mother* repairs boats | Unknown | Feeds later heads | DistilBERT-multi-qa L4H10 |
| 496 | C/F · Final aggregator | Matched documents: *he / she* teaches sailing | Matched documents: *father / mother* repairs boats | Unknown | Score-gap contribution | DistilBERT-multi-qa L5H3 |
| 497 | C/F · Final aggregator | Matched documents: *he / she* teaches sailing | Matched documents: *father / mother* repairs boats | Unknown | Score-gap contribution | DistilBERT-multi-qa L5H11 |
| 498 | C/F · Upstream mediator | Matched documents: *he / she* teaches sailing | Matched documents: *father / mother* repairs boats | Unknown | Feeds later heads | DistilBERT-ms-marco L4H1 |
| 499 | C/F · Upstream mediator | Matched documents: *he / she* teaches sailing | Matched documents: *father / mother* repairs boats | Unknown | Feeds later heads | DistilBERT-ms-marco L4H5 |
| 500 | C/F · Upstream mediator | Matched documents: *he / she* teaches sailing | Matched documents: *father / mother* repairs boats | Unknown | Feeds later heads | DistilBERT-ms-marco L4H10 |
| 501 | C/F · Final aggregator | Matched documents: *he / she* teaches sailing | Matched documents: *father / mother* repairs boats | Unknown | Score-gap contribution | DistilBERT-ms-marco L5H3 |
| 502 | C/F · Final aggregator | Matched documents: *he / she* teaches sailing | Matched documents: *father / mother* repairs boats | Unknown | Score-gap contribution | DistilBERT-ms-marco L5H11 |
| 503 | C · Gender-sensitive mediator | Matched documents: *man / woman* manages a shop | Matched documents: *brother / sister* studies design | Unknown | Feeds L11H3/H11 | BERT-ms-marco L10H6 |
| 504 | C · Gender-sensitive mediator | Matched documents: *man / woman* manages a shop | Matched documents: *brother / sister* studies design | Unknown | Score-gap contribution | BERT-ms-marco L11H3 |
| 505 | C · Gender-sensitive mediator | Matched documents: *man / woman* manages a shop | Matched documents: *brother / sister* studies design | Unknown | Score-gap contribution | BERT-ms-marco L11H11 |
| 506 | C · Gender-sensitive mediator | Matched documents: *man / woman* manages a shop | Matched documents: *brother / sister* studies design | Unknown | Feeds L5H11 | MiniLM-multi-qa L4H3 |
| 507 | C · Gender-sensitive mediator | Matched documents: *man / woman* manages a shop | Matched documents: *brother / sister* studies design | Unknown | Score-gap contribution | MiniLM-multi-qa L5H11 |

### Negation scope: in-scope words reading a negation cue

Table A1; source labels are one-based (RoBERTa-base has 12 heads). These are the best attention-based scope classifiers per model, with limited recall, not complete negation algorithms. Bidirectional encoding permits either temporal direction. No per-head output payload or causal effect was established. [NS]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 508 | R · Scope-to-cue attention | Mira did *not* ⟦open⟧ the gate | Theo *never* ⟦arrived⟧ | Unknown | Unknown | BERT-base L8H4 |
| 509 | R · Scope-to-cue attention | Nia did *not* ⟦drop⟧ the cup | Omar *never* ⟦returned⟧ | Unknown | Unknown | BERT-large L14H4 |
| 510 | R · Scope-to-cue attention | The bell did *not* ⟦ring⟧ | The boat *never* ⟦sailed⟧ | Unknown | Unknown | RoBERTa-base L9H12 |
| 511 | R · Scope-to-cue attention | The door did *not* ⟦close⟧ | The lamp *never* ⟦lit⟧ | Unknown | Unknown | RoBERTa-large L15H15 |

### Vision: demographic-associated outputs and classification tradeoffs

Tables 4–6; zero-based CLIP indices, LAION-2B checkpoint. Italics describe dataset cues, not attention locations. Alignment with demographic text prototypes is not a complete payload explanation. Effects concern the study's occupation classifier. L23H4 appears in both analyses; age results were weak or inconsistent, and ablation did not generally eliminate bias. [GB]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 512 | C/F · Gender-linked classifier contribution | image: *female-presenting clinician* at work | image: *male-presenting clinician* at work | Prototype alignment | Ablation reduces doctor/nurse disparity | CLIP ViT-L/14 L23H4 |
| 513 | C/F · Gender-associated contributor | image: *female-presenting clinician* at work | image: *male-presenting clinician* at work | Prototype alignment | Smaller disparity reduction | CLIP ViT-L/14 L21H2 |
| 514 | C/F · Gender-associated contributor | image: *female-presenting clinician* at work | image: *male-presenting clinician* at work | Prototype alignment | Smaller disparity reduction | CLIP ViT-L/14 L21H10 |
| 515 | C/F · Gender-associated candidate | image: *female-presenting clinician* at work | image: *male-presenting clinician* at work | Prototype alignment | Small mixed ablation effect | CLIP ViT-L/14 L22H14 |
| 516 | F/C · Age-associated candidate | image: *younger-presenting guard* at work | image: *older-presenting guard* at work | Prototype alignment | Small guard-class change | CLIP ViT-L/14 L21H5 |
| 517 | F/C · Age-associated candidate | image: *younger-presenting guard* at work | image: *older-presenting guard* at work | Prototype alignment | Ablation worsens guard disparity | CLIP ViT-L/14 L22H4 |
| 518 | F/C · Age-associated candidate | image: *younger-presenting guard* at work | image: *older-presenting guard* at work | Prototype alignment | Ablation worsens guard disparity | CLIP ViT-L/14 L23H4 |

### Speech: phoneme preferences versus measured classification effects

§4.2–4.4; one-based heads in an added attention classification block above frozen wav2vec 2.0. Phoneme labels schematically describe audio frames. Examples illustrate the studied cue classes; generalization beyond the selected speaking turn was not established. Italics in the last two rows mark task cues, because routing was not decoded. [SA]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 519 | R/C · Vowel-frame preference | ⟦audio frame⟧ reads */U/* | ⟦audio frame⟧ reads */2:/* | Unknown | Pruning harms tested scores | Classifier H5 |
| 520 | R/C · Local phonetic pattern | ⟦audio frame⟧ reads */a m p/* | */a m p/* … ⟦audio frame⟧ | Unknown | Pruning harms tested scores | Classifier H4 |
| 521 | C · Nasality contributor | audio: *nasal resonance* in an utterance | audio: *nasalized segment* in an utterance | Unknown | Pruning lowers nasality F1 | Classifier H13 |
| 522 | C · Tension contributor | audio: *tense articulation* in a phrase | audio: *tension-marked segment* in a phrase | Unknown | Pruning lowers tension F1 | Classifier H10 |

### Speech recognition: similarity-based versus content-based attention

§2.2 and Figure 1 analyze baseline Conformer heads. Families overlap within individual heads. These are frame-to-frame patterns, not word dependencies. Content examples use abstract phoneme labels because no universal preferred phoneme is established. Architectural improvements were evaluated jointly, not as proof of every original head's causal function. [PH]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 523 | R · Phonetic-similarity routing | ⟦/s/ frame⟧ reads */z/ frame* | ⟦/z/ frame⟧ reads */s/ frame* | Unknown | Unknown | Conformer; lower-layer family |
| 524 | R · Query-independent phoneme preference | ⟦phoneme A⟧ reads *preferred phoneme C* | ⟦phoneme B⟧ reads *preferred phoneme C* | Unknown | Unknown | Conformer; lower-layer family |

### A complete small-model inventory: phrase completion, delimiters, and induction

Table 1, Appendix B: all 16 heads in a two-layer attention-only model at the final checkpoint; zero-based. Ablation-selected contexts support contributions, not complete algorithms. Without query brackets, italics mark cues. Roles can change during training. [DH]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 525 | C/R · Prepositional phrase completion | *instead* → of | *because* → of | Unknown | Supports continuation | L0H0 |
| 526 | R · Previous token; names | *Ravi* ⟦Patel⟧ | *Nia* ⟦Moreno⟧ | Unknown | Unknown | L0H1 |
| 527 | C/F · Post-parenthetical completion | Mira *(the guide)* → was | A boat *(the smaller one)* → drifted | Unknown | Supports continuation | L0H2 |
| 528 | C/F · Contiguous phrase completion | *as well* → as | *in order* → to | Unknown | Supports continuation | L0H3 |
| 529 | R · Previous token; dates | *March* ⟦12⟧ | *October* ⟦7⟧ | Unknown | Unknown | L0H4 |
| 530 | R · Current token | a *⟦lantern⟧* | the *⟦garden⟧* | Unknown | Unknown | L0H5 |
| 531 | C/F · Post-quotation completion | *“Come inside,”* → said | *“Wait here,”* → she | Unknown | Supports continuation | L0H6 |
| 532 | C/F · Delimiter support | *(outer [inner] phrase* → ) | *[a, [b, c]* → ] | Unknown | Supports later delimiter head | L0H7 |
| 533 | C/F · Numeric/hyphenated phrases | *three years* → ago | *a once-* → popular | Unknown | Supports continuation | L1H0 |
| 534 | C/R · Comparative completion | *more* useful ⟦th⟧ → an | *more* carefully ⟦th⟧ → an | Unknown | Supports continuation | L1H1 |
| 535 | C/F · Sentence-opening completion | *Finished.␠␠* → The | *He left.␠␠* → She | Unknown | Supports continuation | L1H2 |
| 536 | C/R · Split construction | *neither* rain ⟦fell⟧ → nor | *either* Nia ⟦leaves⟧ → or | Unknown | Supports paired completion | L1H3 |
| 537 | C/F · Phrasal-verb/news completion | *prevent* the boat → from | *keep* the children → safe | Unknown | Supports continuation | L1H4 |
| 538 | C/R · Delimiter matching | *(* a quiet ⟦place⟧ → ) | *[* red, ⟦blue⟧ → ] | Unknown | Supports matching closer | L1H5 |
| 539 | C/R · Code-biased induction | item*:* 3; other code; ⟦item⟧ → : | config*.*size; other code; ⟦config⟧ → . | Continuation evidence | Supports reuse | L1H6 |
| 540 | C/R · General induction | copper *bell* … ⟦copper⟧ → bell | quiet *garden* … ⟦quiet⟧ → garden | Continuation evidence | Supports reuse | L1H7 |


## Further research expansion: entries 541–640

This batch adds physical head instances and reported behavior variants across language, vision, and speech. Repeated family descriptions identify different heads; alternate analyses can describe a previously catalogued head. The entry count is not a count of distinct algorithms. All examples remain illustrative, not fresh experimental measurements.

### Semantic matching and relevance aggregation

C/R evidence. Model: cross-encoder/ms-marco-MiniLM-L-12-v2; zero-based. Soft-TF means graded term matching; matching scores also reflect saturation/length. The BM25-like computation is an approximation. IDF examples assume instrument names are rarer than function words. Thirteen rows instantiate one matching family. [BM]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 541 | Semantic matcher | ⟦lantern⟧ repair [SEP] a *lantern* workshop | ⟦boat⟧ repair [SEP] repairs to a *vessel* | Matching score | Ranking | L0H8 |
| 542 | Semantic matcher | ⟦garden⟧ gate [SEP] the *garden* entrance | ⟦doctor⟧ advice [SEP] a *physician* explains | Matching score | Ranking | L1H7 |
| 543 | Semantic matcher | ⟦river⟧ map [SEP] a *river* chart | ⟦car⟧ repair [SEP] an *automobile* manual | Matching score | Ranking | L2H1 |
| 544 | Semantic matcher | ⟦orchard⟧ pests [SEP] our *orchard* guide | ⟦puppy⟧ food [SEP] meals for a *dog* | Matching score | Ranking | L3H1 |
| 545 | Semantic matcher | ⟦copper⟧ polish [SEP] cleaning *copper* | ⟦ship⟧ guide [SEP] aboard the *vessel* | Matching score | Ranking | L4H9 |
| 546 | Semantic matcher | ⟦bell⟧ repair [SEP] a cracked *bell* | ⟦child⟧ health [SEP] caring for a *kid* | Matching score | Ranking | L5H7 |
| 547 | Semantic matcher | ⟦library⟧ hours [SEP] the *library* timetable | ⟦sofa⟧ cleaning [SEP] wash the *couch* | Matching score | Ranking | L5H9 |
| 548 | Semantic matcher | ⟦pottery⟧ tools [SEP] *pottery* equipment | ⟦bicycle⟧ repair [SEP] fixing a *bike* | Matching score | Ranking | L6H3 |
| 549 | Semantic matcher | ⟦window⟧ latch [SEP] old *window* fittings | ⟦rabbit⟧ care [SEP] feeding a *bunny* | Matching score | Ranking | L6H5 |
| 550 | Semantic matcher | ⟦bridge⟧ history [SEP] the stone *bridge* | ⟦forest⟧ paths [SEP] trails in the *woods* | Matching score | Ranking | L7H9 |
| 551 | Semantic matcher | ⟦music⟧ lesson [SEP] *music* tuition | ⟦teacher⟧ training [SEP] an *educator* guide | Matching score | Ranking | L8H0 |
| 552 | Semantic matcher | ⟦greenhouse⟧ roof [SEP] *greenhouse* repairs | ⟦journey⟧ advice [SEP] planning a *trip* | Matching score | Ranking | L8H1 |
| 553 | Semantic matcher | ⟦sextant⟧ manual [SEP] using a *sextant* | ⟦jewel⟧ care [SEP] polishing a *gem* | Matching score | Ranking | L8H8 |
| 554 | Query redistribution | ⟦repair⟧ the *astrolabe* | ⟦read⟧ the *sextant* manual | Soft-TF | Contextualizes query | L8H10 |
| 555 | Query redistribution | ⟦repair⟧ the *astrolabe* | ⟦read⟧ the *sextant* manual | Soft-TF | Contextualizes query | L9H11 |
| 556 | High-IDF reader | ⟦CLS⟧ repair the *astrolabe* [SEP] … | ⟦CLS⟧ calibrate this *sextant* [SEP] … | Weighted soft-TF | Ranking | L10H1 |
| 557 | Mid/high-IDF reader | ⟦CLS⟧ *repair* the astrolabe [SEP] … | ⟦CLS⟧ *calibrate* this sextant [SEP] … | Weighted soft-TF | Ranking | L10H4 |
| 558 | Mid/high-IDF reader | ⟦CLS⟧ astrolabe *repair* instructions [SEP] … | ⟦CLS⟧ sextant *calibration* instructions [SEP] … | Weighted soft-TF | Ranking | L10H7 |
| 559 | Low-IDF reader | ⟦CLS⟧ repair *the* astrolabe [SEP] … | ⟦CLS⟧ *how* to calibrate sextants [SEP] … | Weighted soft-TF | Ranking | L10H10 |

### Language choice, with checkpoint-specific evidence

Zero-based indices. Adherence = ablation harms expected-language output. Only the two name-reader rows establish the illustrated token route through attention/value interventions. Other italics mark cues, not locations. Last four rows concern base-model translation rankings in Appendix H, not the instruction-tuned checkpoints above. Their payload decomposition remains incomplete. [LC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 560 | C · Name reader | Reply in *German*. Explain rainfall. ⟦Answer:⟧ | Reply in *Spanish*. Describe a garden. ⟦Answer:⟧ | Language identity | Adherence | Qwen2.5-1.5B-Instruct L22H6 |
| 561 | C · Language retention | cue: explain rainfall in *German* | cue: describe a garden in *Spanish* | Language-associated | Adherence | Qwen2.5-3B-Instruct L27H13 |
| 562 | C · Language retention | cue: explain rainfall in *German* | cue: describe a garden in *Spanish* | Unknown | Adherence | Qwen2.5-7B-Instruct L19H1 |
| 563 | C · Language retention | cue: explain rainfall in *German* | cue: describe a garden in *Spanish* | Language-associated | Adherence | Qwen3-1.7B L18H12 |
| 564 | C · Name reader | Reply in *German*. Explain rainfall. ⟦Answer:⟧ | Reply in *Spanish*. Describe a garden. ⟦Answer:⟧ | Language identity | Adherence | Gemma-3-1B-it L11H3 |
| 565 | C · Language retention | cue: explain rainfall in *German* | cue: describe a garden in *Spanish* | Language-associated | Adherence | Gemma-3-4B-it L24H0 |
| 566 | C · Language retention | cue: explain rainfall in *German* | cue: describe a garden in *Spanish* | Language-associated | Adherence | OLMo-2-1B-Instruct L12H8 |
| 567 | C · Requested-language support | cue: explain rainfall in *German* | cue: describe a garden in *Spanish* | Unknown | Adherence | Qwen3-4B L24H27 |
| 568 | C · Requested-language support | cue: explain rainfall in *German* | cue: describe a garden in *Spanish* | Unknown | Adherence | Llama-3.2-1B-Instruct L8H25 |
| 569 | C · Requested-language support | cue: explain rainfall in *German* | cue: describe a garden in *Spanish* | Unknown | Adherence | Llama-3.2-3B-Instruct L13H19 |
| 570 | C · Translation-language selector | cue: English examples paired with *French* translations | cue: English examples paired with *Arabic* translations | Language-associated | Translation language | Qwen3-1.7B-Base L18H12 |
| 571 | C · Translation-language selector | cue: English examples paired with *French* translations | cue: English examples paired with *Arabic* translations | Language-associated | Translation language | Llama-3.2-1B L8H25 |
| 572 | C · Translation-language selector | cue: English examples paired with *French* translations | cue: English examples paired with *Arabic* translations | Language-associated | Translation language | Llama-3.2-1B L9H8 |
| 573 | C · Translation-language selector | cue: English examples paired with *French* translations | cue: English examples paired with *Arabic* translations | Language-associated | Translation language | Gemma-3-1B-pt L15H2 |

### Answer attribution versus other context-circuit attention

Appendix A and J; reported IDs retained. C denotes context-circuit intervention evidence, not proof that every illustrated edge copies the answer. Attribution signal means the attention map can locate supporting text; it is not a decoded value-vector payload. Three figure examples lack explicit head IDs. [EQ]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 574 | R/C · Concentrated answer reader | Mira lives in *Bergen*. Where does Mira live? ⟦Answer:⟧ | The gate code is *cobalt*. What is the code? ⟦Answer:⟧ | Unknown | Attribution signal | Vicuna-7B L18H30 |
| 575 | R · Current-position reader | Mira lives in Bergen. Where does Mira live? *⟦Answer:⟧* | The code is cobalt. What is it? *⟦Answer:⟧* | Unknown | Unknown | Vicuna-7B; Fig. 8 top, ID unspecified |
| 576 | R · Diffuse answer/context reader | *Mira* lives in *Bergen*. Where does Mira live? ⟦Answer:⟧ | *Nia* owns the *bell*. What does Nia own? ⟦Answer:⟧ | Unknown | Unknown | Vicuna-7B; Fig. 8 bottom, ID unspecified |
| 577 | R/C · Answer reader; weak initial-token attention | BOS … The owner is *Nia*. Who owns it? ⟦Answer:⟧ | BOS … The meeting is in *Lima*. Where is it? ⟦Answer:⟧ | Unknown | Attribution signal | Llama-3-8B L17H24 |
| 578 | R/C · Answer and initial-token reader | *BOS* … The owner is *Nia*. Who owns it? ⟦Answer:⟧ | *BOS* … The meeting is in *Lima*. Where is it? ⟦Answer:⟧ | Unknown | Attribution signal | Llama-3-8B L27H20 |
| 579 | R/C · Concentrated answer reader | BOS … Mira carries *rope*. What does she carry? ⟦Answer:⟧ | BOS … Nia repairs *bells*. What does she repair? ⟦Answer:⟧ | Unknown | Attribution signal | Phi-3; Fig. 10, ID unspecified |
| 580 | R/C · Long-context answer reader | The ledger names *Omar*. … Who is named? ⟦Answer:⟧ | The archive lists *Delft*. … Which city is listed? ⟦Answer:⟧ | Unknown | Attribution signal | Llama-3-70B L52H19 |

### Visual output features across four late layers

OpenCLIP ViT-L/14 (LAION-2B), Appendix A.4; zero-based IDs. These are TextSpan output associations, not token-routing claims. Italics mark image cues. Descriptor-aligned means an output component associated with the described feature. Mixed labels preserve heterogeneous descriptions; individual causal effects remain unknown. [TD]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 581 | F: Geography/mixed | image: *rural European lane* beside cottages | image: *New England shore* with a harbor | Descriptor-aligned | Unknown | L20H0 |
| 582 | F: Geography/mixed | image: *tropical island coast* with boats | image: *Arabian cityscape* at dusk | Descriptor-aligned | Unknown | L20H1 |
| 583 | F: Multiplicity | image: *two travelers* beside a bridge | image: *five musicians* on a stage | Descriptor-aligned | Unknown | L20H4 |
| 584 | F: Built-environment | image: *village alley* between houses | image: *airport concourse* full of travelers | Descriptor-aligned | Unknown | L20H6 |
| 585 | F: Geography/scenery | image: *tropical island woodland* beside a stream | image: *glacial landscape* beyond a hut | Descriptor-aligned | Unknown | L20H8 |
| 586 | F: Objects/mixed | image: *ceramic bowl* on a desk | image: *glass bottle* on a shelf | Descriptor-aligned | Unknown | L20H10 |
| 587 | F: Palette | image: a courtyard in *monochrome* | image: a harbor in *muted pastels* | Descriptor-aligned | Unknown | L21H0 |
| 588 | F: Geography | image: a *Dutch canal* behind bicycles | image: an *Australian bush* track at noon | Descriptor-aligned | Unknown | L21H1 |
| 589 | F: People/animals | image: *an infant* beside a blanket | image: *children* gathered around a dog | Descriptor-aligned | Unknown | L21H2 |
| 590 | F: Small-objects | image: *a sewing pin* on dark cloth | image: *a pen* beside an open ledger | Descriptor-aligned | Unknown | L21H7 |
| 591 | F: Social-settings | image: a reader inside *a cafe* | image: a guitarist inside *a music shop* | Descriptor-aligned | Unknown | L21H8 |
| 592 | F: Palette | image: a boat against *blue* water | image: a doorway painted *purple* | Descriptor-aligned | Unknown | L21H9 |
| 593 | F: Geography | image: a town in *Cyprus* beside the sea | image: a street scene in *Seoul* | Descriptor-aligned | Unknown | L21H11 |
| 594 | F: Landscape/mixed | image: *a farmhouse* among fields | image: *a fishing harbor* beside cottages | Descriptor-aligned | Unknown | L21H13 |
| 595 | F: Pattern | image: a rug with *woven geometry* | image: a coat with *houndstooth* panels | Descriptor-aligned | Unknown | L22H0 |
| 596 | F: Geometry | image: a window beneath *a curved arch* | image: a sign shaped like *a triangle* | Descriptor-aligned | Unknown | L22H1 |
| 597 | F: Setting | image: a bench inside *a city park* | image: a passenger inside *a metro station* | Descriptor-aligned | Unknown | L22H2 |
| 598 | F: Objects/body | image: *a jacket* hanging near the door | image: *a helmet* resting on a table | Descriptor-aligned | Unknown | L22H3 |
| 599 | F: Fauna | image: *a dog* beside the greenhouse | image: *a dragonfly* above the pond | Descriptor-aligned | Unknown | L22H6 |
| 600 | F: Season | image: a garden under *winter snow* | image: a path strewn with *autumn leaves* | Descriptor-aligned | Unknown | L22H7 |
| 601 | F: Letterforms | image: a shop sign bearing *V* | image: a gate marker bearing *F* | Descriptor-aligned | Unknown | L22H8 |
| 602 | F: Palette | image: a roof painted *yellow* | image: a boat painted *orange* | Descriptor-aligned | Unknown | L22H10 |
| 603 | F: Palette | image: a tower against *charcoal gray* clouds | image: a portrait rendered in *sepia* | Descriptor-aligned | Unknown | L22H11 |
| 604 | F: Geography | image: a *Thai* street market at dusk | image: a *Spanish* plaza beside a fountain | Descriptor-aligned | Unknown | L22H13 |
| 605 | F: Wildlife/plants | image: *a penguin* beside a rock | image: *a magnolia* beside a path | Descriptor-aligned | Unknown | L23H2 |
| 606 | F: People | image: *siblings* playing beside a gate | image: *an adult* walking through a market | Descriptor-aligned | Unknown | L23H4 |
| 607 | F: Numerosity | image: *six travelers* around a campfire | image: a sign displaying *3* | Descriptor-aligned | Unknown | L23H10 |
| 608 | F: Pattern | image: a scarf with *polka dots* | image: a blanket with *alternating stripes* | Descriptor-aligned | Unknown | L23H12 |

### Query-focused retrieval, selected physical head instances

First four heads in each released NQ configuration; zero-based. Selection measures query-to-relevant-context attention, not answer-token copying. ⟦The whole query⟧ abbreviates aggregation over query positions. Passage scoring is an external use of the maps; payloads and individual causal effects remain unresolved. Each checkpoint contributes four instances of the same family. [QR] [QRC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 609 | R · Query-conditioned retrieval | *Mira planted mint beside the gate.* … ⟦Where did Mira plant mint?⟧ | *Omar left the lantern upstairs.* … ⟦Where is the lantern?⟧ | Unknown | Passage scoring | Llama-3.1-8B-Instruct L14H22 |
| 610 | R · Query-conditioned retrieval | *Nia owns the red boat.* … ⟦Who owns the red boat?⟧ | *Theo repaired the garden pump.* … ⟦Who repaired the pump?⟧ | Unknown | Passage scoring | Llama-3.1-8B-Instruct L13H16 |
| 611 | R · Query-conditioned retrieval | *The library opens at nine.* … ⟦When does the library open?⟧ | *The concert starts at dusk.* … ⟦When does the concert start?⟧ | Unknown | Passage scoring | Llama-3.1-8B-Instruct L14H28 |
| 612 | R · Query-conditioned retrieval | *A storm broke the greenhouse roof.* … ⟦What damaged the roof?⟧ | *A fallen branch blocked the path.* … ⟦What blocked the path?⟧ | Unknown | Passage scoring | Llama-3.1-8B-Instruct L14H31 |
| 613 | R · Query-conditioned retrieval | *Mira planted mint beside the gate.* … ⟦Where did Mira plant mint?⟧ | *Omar left the lantern upstairs.* … ⟦Where is the lantern?⟧ | Unknown | Passage scoring | Llama-3.1-70B-Instruct L31H32 |
| 614 | R · Query-conditioned retrieval | *Nia owns the red boat.* … ⟦Who owns the red boat?⟧ | *Theo repaired the garden pump.* … ⟦Who repaired the pump?⟧ | Unknown | Passage scoring | Llama-3.1-70B-Instruct L35H26 |
| 615 | R · Query-conditioned retrieval | *The library opens at nine.* … ⟦When does the library open?⟧ | *The concert starts at dusk.* … ⟦When does the concert start?⟧ | Unknown | Passage scoring | Llama-3.1-70B-Instruct L35H25 |
| 616 | R · Query-conditioned retrieval | *A storm broke the greenhouse roof.* … ⟦What damaged the roof?⟧ | *A fallen branch blocked the path.* … ⟦What blocked the path?⟧ | Unknown | Passage scoring | Llama-3.1-70B-Instruct L35H21 |
| 617 | R · Query-conditioned retrieval | *Mira planted mint beside the gate.* … ⟦Where did Mira plant mint?⟧ | *Omar left the lantern upstairs.* … ⟦Where is the lantern?⟧ | Unknown | Passage scoring | Llama-3.2-3B-Instruct L13H16 |
| 618 | R · Query-conditioned retrieval | *Nia owns the red boat.* … ⟦Who owns the red boat?⟧ | *Theo repaired the garden pump.* … ⟦Who repaired the pump?⟧ | Unknown | Passage scoring | Llama-3.2-3B-Instruct L12H12 |
| 619 | R · Query-conditioned retrieval | *The library opens at nine.* … ⟦When does the library open?⟧ | *The concert starts at dusk.* … ⟦When does the concert start?⟧ | Unknown | Passage scoring | Llama-3.2-3B-Instruct L13H23 |
| 620 | R · Query-conditioned retrieval | *A storm broke the greenhouse roof.* … ⟦What damaged the roof?⟧ | *A fallen branch blocked the path.* … ⟦What blocked the path?⟧ | Unknown | Passage scoring | Llama-3.2-3B-Instruct L13H21 |
| 621 | R · Query-conditioned retrieval | *Mira planted mint beside the gate.* … ⟦Where did Mira plant mint?⟧ | *Omar left the lantern upstairs.* … ⟦Where is the lantern?⟧ | Unknown | Passage scoring | Qwen2.5-7B-Instruct L16H19 |
| 622 | R · Query-conditioned retrieval | *Nia owns the red boat.* … ⟦Who owns the red boat?⟧ | *Theo repaired the garden pump.* … ⟦Who repaired the pump?⟧ | Unknown | Passage scoring | Qwen2.5-7B-Instruct L16H2 |
| 623 | R · Query-conditioned retrieval | *The library opens at nine.* … ⟦When does the library open?⟧ | *The concert starts at dusk.* … ⟦When does the concert start?⟧ | Unknown | Passage scoring | Qwen2.5-7B-Instruct L16H20 |
| 624 | R · Query-conditioned retrieval | *A storm broke the greenhouse roof.* … ⟦What damaged the roof?⟧ | *A fallen branch blocked the path.* … ⟦What blocked the path?⟧ | Unknown | Passage scoring | Qwen2.5-7B-Instruct L16H14 |

### Rhyme information moved to a line boundary

Gemma-3-27B, §4.1; reported layer/head IDs. These five heads read the preceding rhyme word at the newline. Joint path patching supports a routing role; single-head patches had no measurable effect. The effect column refers to the set, not independent sufficiency of each head. [RH]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 625 | R/C · Rhyme-word→newline | A lantern floated out of *sight*, ⟦newline⟧ | The sparrow settled by the *gate*, ⟦newline⟧ | Rhyme-related signal | Set redirects later rhyme | Gemma-3-27B L30H4 |
| 626 | R/C · Rhyme-word→newline | A lantern floated out of *sight*, ⟦newline⟧ | The sparrow settled by the *gate*, ⟦newline⟧ | Rhyme-related signal | Set redirects later rhyme | Gemma-3-27B L28H14 |
| 627 | R/C · Rhyme-word→newline | A lantern floated out of *sight*, ⟦newline⟧ | The sparrow settled by the *gate*, ⟦newline⟧ | Rhyme-related signal | Set redirects later rhyme | Gemma-3-27B L28H15 |
| 628 | R/C · Rhyme-word→newline | A lantern floated out of *sight*, ⟦newline⟧ | The sparrow settled by the *gate*, ⟦newline⟧ | Rhyme-related signal | Set redirects later rhyme | Gemma-3-27B L30H5 |
| 629 | R/C · Rhyme-word→newline | A lantern floated out of *sight*, ⟦newline⟧ | The sparrow settled by the *gate*, ⟦newline⟧ | Rhyme-related signal | Set redirects later rhyme | Gemma-3-27B L28H29 |

### Rhyme constraints read while composing the next line

Gemma-2-9B-it, §4.6. Two-head patching recovers much of the steering effect in selected examples. The heads read both the rhyme word and its newline; their prediction effects vary across generated positions. Following MLPs translate this information into token preferences. [RP]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 630 | R/C · Rhyme-plan reader | A lantern faded out of *sight*. *newline* The sailor searched ⟦the⟧ … → night | The boat arrived beside the *gate*. *newline* We hoped it was ⟦not⟧ … → late | Rhyme-family constraint | Shapes intermediate token choices | Gemma-2-9B-it L30H3 |
| 631 | R/C · Rhyme-plan reader | A lantern faded out of *sight*. *newline* The sailor searched ⟦the⟧ … → night | The boat arrived beside the *gate*. *newline* We hoped it was ⟦not⟧ … → late | Rhyme-family constraint | Shapes intermediate token choices | Gemma-2-9B-it L31H15 |

### Phonetic retrieval and redundant rhyme support

Llama-3.2-1B-Instruct, §3. Source notation H13L12 means layer 12, head 13. L12H13 has decoded phonetic output evidence. The other two share attention patterns and participate in a redundant ablation-tested set; their individual payloads are less resolved. These are text-only models, not acoustic heads. [PM]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 632 | R/C · Phoneme mover | Give a rhyme for *stone*. ⟦Answer:⟧ → bone | Give a rhyme for *light*. ⟦Answer:⟧ → bright | Phonetically related token directions | Promotes rhyme candidates | Llama-3.2-1B-Instruct L12H13 |
| 633 | R/C · Redundant rhyme-target reader | Give a rhyme for *stone*. ⟦Answer:⟧ → bone | Give a rhyme for *light*. ⟦Answer:⟧ → bright | Unknown individually | Joint ablation disrupts single-token rhymes | Llama-3.2-1B-Instruct L14H21 |
| 634 | R/C · Redundant rhyme-target reader | Give a rhyme for *stone*. ⟦Answer:⟧ → bone | Give a rhyme for *light*. ⟦Answer:⟧ → bright | Unknown individually | Joint ablation disrupts single-token rhymes | Llama-3.2-1B-Instruct L14H22 |

### Speech alignment depends on tokenization

Whisper medium, Figure 5; the plot uses one-based labels (24 decoder layers, 16 heads). First three frequent oracle heads for each tokenization. Oracle selection uses ground-truth boundaries per utterance, so these are not universally best aligners. Italics mark the corresponding audio span; ⟦…⟧ marks a decoder alignment row. DTW is external timestamp extraction, not an inferred value-vector payload. [WA]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 635 | R · Wordpiece/audio alignment | audio: ring the *bell*; ⟦text position for bell⟧ | audio: open the *gate*; ⟦text position for gate⟧ | Unknown | Map supports DTW timestamps | Whisper-medium L17H16 |
| 636 | R · Wordpiece/audio alignment | audio: ring the *bell*; ⟦text position for bell⟧ | audio: open the *gate*; ⟦text position for gate⟧ | Unknown | Map supports DTW timestamps | Whisper-medium L23H1 |
| 637 | R · Wordpiece/audio alignment | audio: ring the *bell*; ⟦text position for bell⟧ | audio: open the *gate*; ⟦text position for gate⟧ | Unknown | Map supports DTW timestamps | Whisper-medium L18H16 |
| 638 | R · Character/audio alignment | audio: *bell*; ⟦character rows b e l l⟧ | audio: *gate*; ⟦character rows g a t e⟧ | Unknown | Map supports DTW timestamps | Whisper-medium L9H6 |
| 639 | R · Character/audio alignment | audio: *bell*; ⟦character rows b e l l⟧ | audio: *gate*; ⟦character rows g a t e⟧ | Unknown | Map supports DTW timestamps | Whisper-medium L20H9 |
| 640 | R · Character/audio alignment | audio: *bell*; ⟦character rows b e l l⟧ | audio: *gate*; ⟦character rows g a t e⟧ | Unknown | Map supports DTW timestamps | Whisper-medium L17H4 |

## Additional researched entries: 641–740

Added 2026-11-05: 100 entries from eight research sources and two supporting author repositories. This batch includes physical-head instances, position-specific computations, head–concept associations, and explicitly labeled families. The 52 diffusion-ranking rows are associations across two models; they are not 52 newly decoded algorithms.

### Arithmetic: position-specific head/MLP computations

The two-layer, three-head addition model in Appendices I–J, especially Table 13. These are **12 position-specific computations**, not 12 distinct physical heads. Labels are zero-based; P is the query position. Digits D0/A0 are units. SA denotes a sum modulo ten; ST classifies pair sums as below nine, nine, or above nine; ST2/ST4 incorporate lower-place carries. Payloads below belong to the **joint head-and-MLP computation**; its exact division is unresolved. Italics identify operand sources, not every intermediate dependency. [AV]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 641 | T/C · Hundreds carry classification | 5 2 *7* 8 6 + 4 8 *⟦2⟧* | 1 8 *3* 4 2 + 2 2 *⟦6⟧* | A2.ST; joint | A4, A5 prediction | Addition toy P8.L0.H1 + MLP |
| 642 | T/C · Tens carry classification | 5 2 7 *8* 6 + 4 8 2 *⟦3⟧* | 1 8 3 *4* 2 + 2 2 6 *⟦7⟧* | A1.ST; joint | A3–A5 prediction | Addition toy P9.L0.H1 + MLP |
| 643 | T/C · Units-to-tens carry composition | 5 2 7 8 *6* + 4 8 2 3 *⟦5⟧* | 1 8 3 4 *2* + 2 2 6 7 *⟦9⟧* | A1.ST2; joint | A2–A5 prediction | Addition toy P10.L0.H1 + MLP |
| 644 | T/C · Thousands carry composition | 5 *2* 7 8 6 + 4 *8* 2 3 5 ⟦=⟧ | 1 *8* 3 4 2 + 2 *2* 6 7 9 ⟦=⟧ | A3.ST4; joint | A5 prediction | Addition toy P11.L0.H1 + MLP |
| 645 | T/C · Ten-thousands carry classification | *5* 2 7 8 6 + *4* 8 2 3 5 ⟦=⟧ | *1* 8 3 4 2 + *2* 2 6 7 9 ⟦=⟧ | A4.ST; joint | A5 prediction | Addition toy P11.L0.H2 + MLP |
| 646 | T/C · Ten-thousands base sum | *5* 2 7 8 6 + *4* 8 2 3 5 = ⟦1⟧ | *1* 8 3 4 2 + *2* 2 6 7 9 = ⟦0⟧ | A4.SA; joint | A4 prediction | Addition toy P12.L0.H0+H2 + MLP |
| 647 | T/C · Thousands base sum | 5 *2* 7 8 6 + 4 *8* 2 3 5 = 1 ⟦0⟧ | 1 *8* 3 4 2 + 2 *2* 6 7 9 = 0 ⟦4⟧ | A3.SA; joint | A3 prediction | Addition toy P13.L0.H0+H2 + MLP |
| 648 | T/C · Hundreds base sum | 5 2 *7* 8 6 + 4 8 *2* 3 5 = 1 0 ⟦1⟧ | 1 8 *3* 4 2 + 2 2 *6* 7 9 = 0 4 ⟦1⟧ | A2.SA; joint | A2 prediction | Addition toy P14.L0.H0+H2 + MLP |
| 649 | T/C · Tens carry recomputation | 5 2 7 *8* 6 + 4 8 2 *3* 5 = 1 0 ⟦1⟧ | 1 8 3 *4* 2 + 2 2 6 *7* 9 = 0 4 ⟦1⟧ | Local carry plus P10 correction; joint | A2 prediction | Addition toy P14.L0.H1 + MLP |
| 650 | T/C · Tens base sum | 5 2 7 *8* 6 + 4 8 2 *3* 5 = 1 0 1 ⟦0⟧ | 1 8 3 *4* 2 + 2 2 6 *7* 9 = 0 4 1 ⟦0⟧ | A1.SA; joint | A1 prediction | Addition toy P15.L0.H0+H2 + MLP |
| 651 | T/C · Units carry | 5 2 7 8 *6* + 4 8 2 3 *5* = 1 0 1 ⟦0⟧ | 1 8 3 4 *2* + 2 2 6 7 *9* = 0 4 1 ⟦0⟧ | A0.SC; joint | A1 prediction | Addition toy P15.L0.H1 + MLP |
| 652 | T/C · Units base sum | 5 2 7 8 *6* + 4 8 2 3 *5* = 1 0 1 0 ⟦2⟧ | 1 8 3 4 *2* + 2 2 6 7 *9* = 0 4 1 0 ⟦2⟧ | A0.SA; joint | A0 prediction | Addition toy P16.L0.H0+H2 + MLP |

### Name-associated pronoun information passed through a summary position

GPT-2 Small, Appendix K and Figure 22. Circuit discovery, attention inspection, and path patching support this pathway. The task measures stereotyped **name-associated pronoun expectations**, not a person's actual gender. Indices are zero-based. The intervening MLPs matter. [GD]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 653 | R/C · Name-position preprocessing | *⟦Laura⟧* is very patient, isn't | *⟦Robert⟧* is very patient, isn't | Name signal | Supplies later readers | GPT-2 Small L0H4 |
| 654 | R/C · Name→copula relay | *Laura* ⟦is⟧ very patient, isn't | *Robert* ⟦is⟧ very patient, isn't | Name-associated pronoun information | Feeds MLP7 at copula | GPT-2 Small L4H3 |
| 655 | R/C · Name→copula relay | *Laura* ⟦is⟧ very patient, isn't | *Robert* ⟦is⟧ very patient, isn't | Name-associated pronoun information | Feeds MLP7 at copula | GPT-2 Small L6H0 |
| 656 | R/C · Copula→completion relay | Laura *is* very patient, isn'⟦t⟧ → she | Robert *is* very patient, isn'⟦t⟧ → he | Pronoun-associated signal | Supports expected completion | GPT-2 Small L9H7 |
| 657 | R/C · Copula→completion relay | Laura *is* very patient, isn'⟦t⟧ → she | Robert *is* very patient, isn'⟦t⟧ → he | Pronoun-associated signal | Supports expected completion | GPT-2 Small L10H9 |

### Compiled RASP operations with explicit source selectors

ACDC Appendix I/Figure 21 and the Tracr program definition. These are compiler-created weights, not behaviors learned from prose. Labels follow the circuit figure. Reverse is bidirectional; the fraction includes the current position and excludes BOS. [GD] [TC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 658 | T · Prefix indicator averaging | *x a* *⟦x⟧* → 2/3 | *a b x* *⟦b⟧* → 1/4 | Mean of x-indicators | Writes prefix fraction | Tracr xproportion a1.0 |
| 659 | T · Reflected-index retrieval | ⟦a⟧ b c *d* → d | a ⟦b⟧ *c* d → c | Token at n−1−i | Writes reversed sequence | Tracr reverse a3.0 |

### Diffusion concept sensitivity: SD1.4 head rankings

Top-ranked head for each listed concept in the authors' released HRV data, pinned to commit `b2e4e90`. HRV measures query/key preference against injected concept-word keys; **italics mark test cues, not verified natural-prompt attention maps**. No value-vector decoding follows from this ranking. Ordered weakening validates some concept-specific head sets, not each head independently. Counting, lighting, and expression categories are omitted here because the paper flags validation difficulties. [HR] [HC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 660 | F · Animals | a *badger* beside a stump | an *otter* on a riverbank | Unknown | Unknown individually | SD1.4 up8/H3 |
| 661 | F · Plants | a *fern* in a clay pot | an *orchid* near a window | Unknown | Unknown individually | SD1.4 up2/H3 |
| 662 | F · Fruits and Vegetables | *apricots* in a basket | a pile of *radishes* | Unknown | Unknown individually | SD1.4 up7/H5 |
| 663 | F · People | a *sailor* beside a pier | a *dancer* on a stage | Unknown | Unknown individually | SD1.4 down2/H4 |
| 664 | F · Vehicles | a *tram* crossing a bridge | a *scooter* beside a wall | Unknown | Unknown individually | SD1.4 up3/H5 |
| 665 | F · Buildings | a *lighthouse* above a cliff | a *chapel* in a valley | Unknown | Unknown individually | SD1.4 down3/H2 |
| 666 | F · Furniture | an *ottoman* by the fire | a *sideboard* against a wall | Unknown | Unknown individually | SD1.4 down2/H6 |
| 667 | F · Electronics | a *radio* on a shelf | a *projector* on a desk | Unknown | Unknown individually | SD1.4 up6/H3 |
| 668 | F · Clothing | a wool *coat* on a hook | a silk *scarf* on a chair | Unknown | Unknown individually | SD1.4 down4/H4 |
| 669 | F · Accessories | a *brooch* on velvet | a *wristwatch* beside a cup | Unknown | Unknown individually | SD1.4 down4/H4 |
| 670 | F · Tools | a *chisel* on a bench | a *spanner* beside a wheel | Unknown | Unknown individually | SD1.4 up0/H1 |
| 671 | F · Toys | a wooden *doll* on a shelf | a *spinning top* on the floor | Unknown | Unknown individually | SD1.4 down5/H2 |
| 672 | F · Food and Beverages | a bowl of *stew* | a glass of *lemonade* | Unknown | Unknown individually | SD1.4 up3/H4 |
| 673 | F · Books and Documents | a *journal* beside a candle | a folded *map* on a table | Unknown | Unknown individually | SD1.4 down0/H5 |
| 674 | F · Sports Equipment | a *hockey stick* near a locker | a *badminton racket* on grass | Unknown | Unknown individually | SD1.4 down5/H5 |
| 675 | F · Musical Instruments | a *cello* in a room | an *oboe* on a stand | Unknown | Unknown individually | SD1.4 down5/H6 |
| 676 | F · Written Characters | a sign bearing *K* | a tile marked *7* | Unknown | Unknown individually | SD1.4 down0/H6 |
| 677 | F · Color | a *crimson* lantern | a *lavender* door | Unknown | Unknown individually | SD1.4 up8/H0 |
| 678 | F · Shape | a *triangular* window | a *hexagonal* box | Unknown | Unknown individually | SD1.4 mid0/H5 |
| 679 | F · Texture | a *ribbed* vase | a *pebbled* wall | Unknown | Unknown individually | SD1.4 mid0/H6 |
| 680 | F · Size | a *tiny* cottage | an *enormous* cup | Unknown | Unknown individually | SD1.4 mid0/H2 |
| 681 | F · Image Style | an *etching* of a harbor | a *mosaic* of a bird | Unknown | Unknown individually | SD1.4 mid0/H3 |
| 682 | F · Material | a *porcelain* bell | a *brass* lantern | Unknown | Unknown individually | SD1.4 up2/H0 |
| 683 | F · Facial Features | a face with a *beard* | a face with *freckles* | Unknown | Unknown individually | SD1.4 down2/H4 |
| 684 | F · Poses and Gestures | a person *kneeling* | a person *waving* | Unknown | Unknown individually | SD1.4 mid0/H2 |
| 685 | F · Nature Scenes | a *ravine* in sunlight | a *lagoon* under clouds | Unknown | Unknown individually | SD1.4 down5/H0 |
| 686 | F · Weather Conditions | a street in *hail* | a field in *mist* | Unknown | Unknown individually | SD1.4 up0/H6 |
| 687 | F · Time of Day | a harbor at *dawn* | a garden at *midnight* | Unknown | Unknown individually | SD1.4 mid0/H2 |
| 688 | F · Geo-locations | a street in *Lisbon* | a canal in *Venice* | Unknown | Unknown individually | SD1.4 up2/H1 |
| 689 | F · Brand Logos | a cap bearing a *Puma logo* | a shirt bearing a *Reebok logo* | Unknown | Unknown individually | SD1.4 down4/H2 |
| 690 | F · Geometric Patterns | a blanket with *zigzags* | a vase with *chevrons* | Unknown | Unknown individually | SD1.4 down0/H1 |

### Diffusion concept sensitivity: SDXL head rankings

First ranked head in each selected SDXL top-11 list, from the same pinned release. `down`, `mid`, and `up` name U-Net regions; numbers are **zero-based cross-attention layer counters within each region**, followed by the head index. These are separate model instances of concept sensitivity, not additional algorithms. Shared IDs across concepts remain separate head–concept associations. [HC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 691 | F · Animals | a *badger* beside a stump | an *otter* on a riverbank | Unknown | Unknown individually | SDXL down18/H4 |
| 692 | F · Plants | a *fern* in a clay pot | an *orchid* near a window | Unknown | Unknown individually | SDXL mid7/H4 |
| 693 | F · Fruits and Vegetables | *apricots* in a basket | a pile of *radishes* | Unknown | Unknown individually | SDXL up18/H15 |
| 694 | F · People | a *sailor* beside a pier | a *dancer* on a stage | Unknown | Unknown individually | SDXL up22/H2 |
| 695 | F · Vehicles | a *tram* crossing a bridge | a *scooter* beside a wall | Unknown | Unknown individually | SDXL down16/H12 |
| 696 | F · Buildings | a *lighthouse* above a cliff | a *chapel* in a valley | Unknown | Unknown individually | SDXL down14/H15 |
| 697 | F · Furniture | an *ottoman* by the fire | a *sideboard* against a wall | Unknown | Unknown individually | SDXL mid6/H10 |
| 698 | F · Electronics | a *radio* on a shelf | a *projector* on a desk | Unknown | Unknown individually | SDXL down15/H8 |
| 699 | F · Clothing | a wool *coat* on a hook | a silk *scarf* on a chair | Unknown | Unknown individually | SDXL up20/H5 |
| 700 | F · Accessories | a *brooch* on velvet | a *wristwatch* beside a cup | Unknown | Unknown individually | SDXL down22/H1 |
| 701 | F · Tools | a *chisel* on a bench | a *spanner* beside a wheel | Unknown | Unknown individually | SDXL down22/H9 |
| 702 | F · Toys | a wooden *doll* on a shelf | a *spinning top* on the floor | Unknown | Unknown individually | SDXL down17/H4 |
| 703 | F · Food and Beverages | a bowl of *stew* | a glass of *lemonade* | Unknown | Unknown individually | SDXL mid4/H6 |
| 704 | F · Books and Documents | a *journal* beside a candle | a folded *map* on a table | Unknown | Unknown individually | SDXL down1/H2 |
| 705 | F · Sports Equipment | a *hockey stick* near a locker | a *badminton racket* on grass | Unknown | Unknown individually | SDXL mid7/H1 |
| 706 | F · Musical Instruments | a *cello* in a room | an *oboe* on a stand | Unknown | Unknown individually | SDXL up27/H13 |
| 707 | F · Written Characters | a sign bearing *K* | a tile marked *7* | Unknown | Unknown individually | SDXL mid9/H8 |
| 708 | F · Color | a *crimson* lantern | a *lavender* door | Unknown | Unknown individually | SDXL up14/H6 |
| 709 | F · Shape | a *triangular* window | a *hexagonal* box | Unknown | Unknown individually | SDXL mid7/H18 |
| 710 | F · Texture | a *ribbed* vase | a *pebbled* wall | Unknown | Unknown individually | SDXL down12/H10 |
| 711 | F · Material | a *porcelain* bell | a *brass* lantern | Unknown | Unknown individually | SDXL mid7/H17 |

### Genomic heads: promoter positions and sequence motifs

The curated-data genomic Transformer-XL model, Figure 3 and accompanying analysis. Layer/head labels below are the paper's **one-based** labels. Convolution gives each source a seven-base neighborhood. Examples are schematic promoter contexts: numbers are offsets from a candidate transcription start site (TSS). Motif resemblance suggests biological associations; it does not establish binding or causation. [GE]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 712 | R · −10 promoter region | … *TATAAT near −10* … ⟦candidate TSS⟧ | … *TATAAT between −12 and −6* … ⟦candidate TSS⟧ | Unknown | Unknown | Genomic Transformer-XL L2H1 |
| 713 | R · −10 promoter region | … *TATAAT near −10* … ⟦candidate TSS⟧ | … *TATAAT between −12 and −6* … ⟦candidate TSS⟧ | Unknown | Unknown | Genomic Transformer-XL L2H2 |
| 714 | R · −35 promoter region | … *TTGACA near −35* … ⟦candidate TSS⟧ | … *TTGACA upstream* … ⟦candidate TSS⟧ | Unknown | Unknown | Genomic Transformer-XL Fig. 3B |
| 715 | R · Downstream edge of −10 region | … −10 … *GGGA near −6/−5* … ⟦candidate TSS⟧ | … *GGGA after −10 element* … ⟦candidate TSS⟧ | Unknown | Unknown | Genomic Transformer-XL Fig. 3C |
| 716 | R · Extended −10-associated region | … *TGA near −15* … ⟦candidate TSS⟧ | … *TGC near −15* … ⟦candidate TSS⟧ | Unknown; biological assignment ambiguous | Unknown | Genomic Transformer-XL Fig. 3D |
| 717 | R · ArcA-like sequence | … *TGTTAA* … ⟦candidate TSS⟧ | … *GT-rich motif in promoter* … ⟦candidate TSS⟧ | Unknown | Unknown | Genomic Transformer-XL Fig. 3E |
| 718 | R · FecI-like sequence | … *GGAAAT* … ⟦candidate TSS⟧ | … *GGAAAT at another upstream position* … ⟦candidate TSS⟧ | Unknown | Unknown | Genomic Transformer-XL Fig. 3F |
| 719 | R · Fixed upstream region | … *region at −82* … ⟦candidate TSS⟧ | … *−82 neighborhood in another promoter* … ⟦candidate TSS⟧ | Unknown; several candidate regulators | Unknown | Genomic Transformer-XL L6H1 |

### Video attention: spatial and temporal selection patterns

Compact Attention §3.2/Figure 3. Seven pattern variants within the reported families, not seven identified physical heads. Studied models include Wan2.1 and Hunyuan. Spatial and temporal patterns can coexist in one head. Values are not semantically decoded; preserving these patterns supports sparse computation, which does not establish each pattern's native causal role. [VA]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 720 | R · Spatial neighborhood | ⟦patch on lantern⟧ → *nearby patches* | ⟦patch on boat⟧ → *surrounding patches* | Unknown | Unknown | Video DiT; local family |
| 721 | R · Horizontal/vertical corridors | ⟦patch at row r, column c⟧ → *row r and column c* | ⟦center patch⟧ → *cross-shaped region* | Unknown | Unknown | Video DiT; cross-shaped family |
| 722 | R · Broad spatial field | ⟦door patch⟧ → *whole frame* | ⟦tree patch⟧ → *whole frame* | Unknown | Unknown | Video DiT; global family |
| 723 | R · Salient-object concentration | ⟦query patch⟧ → *prominent boat region* | ⟦query patch⟧ → *prominent bird region* | Unknown | Unknown | Video DiT; input-dependent global variant |
| 724 | R · Nearby-frame preference | ⟦frame 8 patch⟧ → *frames near 8* | ⟦frame 20 patch⟧ → *frames near 20* | Unknown | Unknown | Video DiT; temporal-decay variant |
| 725 | R · Nonlocal frame-distance preference | ⟦frame t patch⟧ → *frames at favored nonzero distance* | ⟦frame u patch⟧ → *favored distant frames* | Unknown | Unknown | Video DiT; temporal-distance variant |
| 726 | R · Frame-distance invariant | ⟦frame 8 patch⟧ → *similar spatial pattern across frames* | ⟦frame 20 patch⟧ → *similar spatial pattern across frames* | Unknown | Unknown | Video DiT; time-invariant family |

### Video heads: motion correspondence versus structural features

HALO §3, Figure 4, and Appendix D. Individual labels use the paper's notation. Motion is inferred from attention-derived displacement fields; this is not proof that values literally contain optical-flow vectors. Interventions select head sets. [HM]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 727 | R/C · Cross-frame correspondence | ⟦boat patch in frame t⟧ → *boat patch in frame u* | ⟦bird patch in frame t⟧ → *bird patch in frame u* | Unknown; map yields displacement | Set guides motion transfer | CogVideoX temporal-head family |
| 728 | R/C · Concentrated spatial correspondence | ⟦patch i⟧ → *corresponding local patch* | ⟦patch j⟧ → *corresponding local patch* | Structure-associated features | Selected set supports layout transfer | CogVideoX L20H8 |
| 729 | R · Diffuse spatial attention | ⟦patch i⟧ → *scattered visual positions* | ⟦patch j⟧ → *broad irregular region* | Less spatially concentrated features | Unknown individually | CogVideoX L20H6 |
| 730 | R/C · Cross-frame correspondence; replication | ⟦cart patch in frame t⟧ → *cart patch in frame u* | ⟦runner patch in frame t⟧ → *runner patch in frame u* | Unknown; map yields displacement | Set guides motion transfer | Wan temporal-head family |

### Vision-language output associations at identified heads

LLaVA-1.5-7B, Figure 8/Appendix C.2, zero-based IDs. These nine distinct heads appear among the example-specific top-five attribution rankings. **Italics mark image-content cues, not localized attention targets.** Feature labels summarize logit-lens vocabulary associations; they do not establish complete OV algorithms. Some heads recur under different images with different readouts. New illustrations below are hypotheses for recognizing these conditional behaviors, not additional measured examples. [VI]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 731 | F · Object-dependent readout | image: *dog by a stream*; identify object | image: *iced pastry on a plate*; identify object | Dog / bakery associations | Unknown individually | LLaVA-1.5-7B L15H22 |
| 732 | F · Object-dependent readout | image: *dog in a meadow*; identify object | image: *sweet pastry in a window*; identify object | Dog / bakery associations | Unknown individually | LLaVA-1.5-7B L20H5 |
| 733 | F · Scene-dependent readout | image: *boat beside a jetty*; identify object | image: *dog at a lakeside*; identify object | Marine / nature associations | Unknown individually | LLaVA-1.5-7B L14H29 |
| 734 | F · Animal/photo readout | image: *dog beside a fence*; identify object | image: *dog on a path*; identify object | Animal / photography associations | Unknown individually | LLaVA-1.5-7B L16H4 |
| 735 | F · Floating-vessel readout | image: *boat on a canal*; identify object | image: *boat in a cove*; identify object | Vessel / flotation associations | Unknown individually | LLaVA-1.5-7B L17H9 |
| 736 | F · Aquatic-context readout | image: boat on *water*; identify object | image: boat beside a *shore*; identify object | Aquatic associations | Unknown individually | LLaVA-1.5-7B L18H12 |
| 737 | F · Watercraft readout | image: *boat at a pier*; identify object | image: *boat on a lake*; identify object | Watercraft associations | Unknown individually | LLaVA-1.5-7B L20H12 |
| 738 | F · Object-dependent readout | image: *boat beneath a bridge*; identify object | image: *round pastry on a tray*; identify object | Watercraft / bakery associations | Unknown individually | LLaVA-1.5-7B L17H18 |
| 739 | F · Baked-food readout | image: *iced pastry beside a cup*; identify object | image: *pastry on baking paper*; identify object | Bakery associations | Unknown individually | LLaVA-1.5-7B L17H30 |

### Spelling-conditioned retrieval of a country representation

Figure 93 combines observed attention with J-lens projections of Q/K/V/O weights. The proposed country payload is supported by those projections; nationality disambiguation remains the authors' hypothesis. This does not assign a nationality to every writer using British spelling. [JL]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 740 | R/F · British spelling→country cue | The *Canadian* guide admired the ⟦colour⟧. | The *Australian* visitor reached the ⟦centre⟧. | Country-associated representation; inferred | Possible nationality disambiguation; untested | Claude study Fig. 93; head ID unstated |

## Additional researched entries: 741–840

Added 2026-11-05: 100 entries drawing on six additional papers and a further pass through Appendix M. This batch emphasizes language, factual recall, tool-format readout, and logical reasoning. Physical instances of the same role and conditional behaviors are explicitly distinguished from new algorithms. All examples remain newly composed illustrations.

### More Appendix M associations: early syntax through later concepts

Table 5, GPT-2 Small. These are heuristic SAE associations, not complete head algorithms. Italics mark cues, **not verified attention targets**; even familiar labels remain associations here. “Agreement” means agreeing in discourse. Indices are zero-based. [M]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 741 | F · Of-context | a bowl *of* cherries | the rim *of* a cup | Associated cue; not fully decoded | Unknown | GPT-2 Small L0H1 |
| 742 | F · Duplicate cue | *marble* … *marble* | *violet* … *violet* | Associated cue; not fully decoded | Unknown | GPT-2 Small L0H5 |
| 743 | F · Sequence/pair cue | *four, five* | *left, right* | Associated cue; not fully decoded | Unknown | GPT-2 Small L1H5 |
| 744 | F · Predicate continuation | *never* entered the tower | *just* opened the parcel | Associated cue; not fully decoded | Unknown | GPT-2 Small L2H0 |
| 745 | F · Entity–action cue | *council approved* the plan | *company released* a report | Associated cue; not fully decoded | Unknown | GPT-2 Small L2H9 |
| 746 | F · Duplicate cue | *copper* … *copper* | *ribbon* … *ribbon* | Associated cue; not fully decoded | Unknown | GPT-2 Small L3H0 |
| 747 | F · Predicate–subject cue | *such* a bright morning | *how* the wheel turns | Associated cue; not fully decoded | Unknown | GPT-2 Small L3H2 |
| 748 | F · Government/extremity cue | *ministry* of transport | the *most severe* frost | Associated cue; not fully decoded | Unknown | GPT-2 Small L3H6 |
| 749 | F · Typicality/extremity cue | a *typical* spring day | an *extremely* steep path | Associated cue; not fully decoded | Unknown | GPT-2 Small L4H5 |
| 750 | F · Weak duplicate cue | *maple* … *maple* | *cobalt* … *cobalt* | Associated cue; not fully decoded | Unknown | GPT-2 Small L4H7 |
| 751 | F · Previous-token association | *green* door | *silver* spoon | Associated cue; not fully decoded | Unknown | GPT-2 Small L4H11 |
| 752 | F · Induction association | amber *moth* … amber | cedar *box* … cedar | Associated cue; not fully decoded | Unknown | GPT-2 Small L5H5 |
| 753 | F · Post-comma verb cue | She paused, then *reached* | He turned, and *asked* | Associated cue; not fully decoded | Unknown | GPT-2 Small L6H3 |
| 754 | F · Discourse agreement cue | *I agree* with that proposal | *That is right*, she said | Associated cue; not fully decoded | Unknown | GPT-2 Small L6H5 |
| 755 | F · Verb/phrase suffix cue | the latch was open*ed* | the room was empt*ied* | Associated cue; not fully decoded | Unknown | GPT-2 Small L6H11 |
| 756 | F · Nonstandard induction association | *al-* … *al-* | *re-* … *re-* | Associated cue; not fully decoded | Unknown | GPT-2 Small L7H2 |
| 757 | F · Situation/action cue | the *decision to* leave | the *situation is* improving | Associated cue; not fully decoded | Unknown | GPT-2 Small L7H8 |
| 758 | F · Induction association | cobalt *ring* … cobalt | ivory *vase* … ivory | Associated cue; not fully decoded | Unknown | GPT-2 Small L7H10 |
| 759 | F · Preposition-copy association | speak *with* … speak | wait *for* … wait | Associated cue; not fully decoded | Unknown | GPT-2 Small L8H1 |
| 760 | F · Time/focus/eyes cue | *time* slipped away | her *eyes* narrowed | Associated cue; not fully decoded | Unknown | GPT-2 Small L9H0 |
| 761 | F · Abstract concept continuation | a difficult *diagnosis* | concerns about *safety* | Associated cue; not fully decoded | Unknown | GPT-2 Small L9H2 |
| 762 | F · Name-copy association | *Elara* … Elara | *Jonas* … Jonas | Associated cue; not fully decoded | Unknown | GPT-2 Small L9H9 |
| 763 | F · Relational connector cue | from the hill *to* the shore | aided *by* a neighbor | Associated cue; not fully decoded | Unknown | GPT-2 Small L9H10 |
| 764 | F · Title cue | *Chief Justice* Vale | *Prime Minister* Rowan | Associated cue; not fully decoded | Unknown | GPT-2 Small L10H6 |
| 765 | F · Induction association | scarlet *thread* … scarlet | bronze *key* … bronze | Associated cue; not fully decoded | Unknown | GPT-2 Small L6H9 |
| 766 | F · Long-context association | At dawn, *Elara promised to return*. … By dusk, she was still away. | The map marked *a hidden southern gate*. … Hours later, the travelers arrived. | Context-tracking association | Unknown; calibration conjectured | GPT-2 Small L11H3 |

### Retrieval and induction across independently trained models

Sections 4–5 of the spectral-screening preprint. TS-51M is seed 42 at step 4000; Karpathy124M is the FineWeb checkpoint at step 17600, **not OpenAI GPT-2**. Pythia labels are separate checkpoints. Indices are zero-based. Set ablation does not prove each member necessary. L11H14 also strongly attends BOS; examples show its induction component. [SX]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 767 | R/C · KEY retrieval | KEY *zup* … ⟦QUERY⟧ → zup | KEY *dak* … ⟦QUERY⟧ → dak | Codeword-related; inferred | Retrieval; set ablation | TS-51M s42 L0H3 |
| 768 | R/C · KEY retrieval | KEY *zup* … ⟦QUERY⟧ → zup | KEY *dak* … ⟦QUERY⟧ → dak | Codeword-related; inferred | Retrieval; set ablation | TS-51M s42 L0H6 |
| 769 | R/C · KEY retrieval | KEY *zup* … ⟦QUERY⟧ → zup | KEY *dak* … ⟦QUERY⟧ → dak | Codeword-related; inferred | Retrieval; set ablation | TS-51M s42 L0H14 |
| 770 | R/C · KEY retrieval | KEY *zup* … ⟦QUERY⟧ → zup | KEY *dak* … ⟦QUERY⟧ → dak | Codeword-related; inferred | Retrieval; set ablation | TS-51M s42 L0H15 |
| 771 | R/C · Induction | amber *knot* … ⟦amber⟧ → knot | birch *lid* … ⟦birch⟧ → lid | Unknown exact payload | Individual ablation impairs induction | Karpathy124M L8H5 |
| 772 | R · Induction | amber *knot* … ⟦amber⟧ → knot | birch *lid* … ⟦birch⟧ → lid | Unknown exact payload | Circuit-level support | Karpathy124M L8H6 |
| 773 | R/C · Induction | amber *knot* … ⟦amber⟧ → knot | birch *lid* … ⟦birch⟧ → lid | Unknown exact payload | Individual ablation impairs induction | Karpathy124M L8H8 |
| 774 | R/C · Induction | amber *knot* … ⟦amber⟧ → knot | birch *lid* … ⟦birch⟧ → lid | Unknown exact payload | Individual ablation impairs induction | Karpathy124M L8H10 |
| 775 | R · Induction | amber *knot* … ⟦amber⟧ → knot | birch *lid* … ⟦birch⟧ → lid | Unknown exact payload | Circuit-level support | Karpathy124M L7H4 |
| 776 | R · Previous token | the *small* ⟦gate⟧ | a *wooden* ⟦shelf⟧ | Unknown | Weak individual induction effect | Karpathy124M L6H10 |
| 777 | R · Previous token | the *small* ⟦gate⟧ | a *wooden* ⟦shelf⟧ | Unknown | Weak individual induction effect | Karpathy124M L1H9 |
| 778 | R · Previous token | the *small* ⟦gate⟧ | a *wooden* ⟦shelf⟧ | Unknown | Weak individual induction effect | Karpathy124M L1H11 |
| 779 | R · Previous token | the *small* ⟦gate⟧ | a *wooden* ⟦shelf⟧ | Unknown | Unknown | Karpathy124M L6H9 |
| 780 | R · Previous token | her *blue* ⟦coat⟧ | the *old* ⟦mill⟧ | Unknown | Unknown | Pythia-160M L3H2 |
| 781 | R · Previous token | her *blue* ⟦coat⟧ | the *old* ⟦mill⟧ | Unknown | Unknown | Pythia-410M L5H2 |
| 782 | R/C · Induction | linen *bag* … ⟦linen⟧ → bag | willow *basket* … ⟦willow⟧ → basket | Unknown exact payload | Set-ablation support | Pythia-160M L8H2 |
| 783 | R/C · Induction | linen *bag* … ⟦linen⟧ → bag | willow *basket* … ⟦willow⟧ → basket | Unknown exact payload | Set-ablation support | Pythia-160M L5H0 |
| 784 | R/C · Induction | linen *bag* … ⟦linen⟧ → bag | willow *basket* … ⟦willow⟧ → basket | Unknown exact payload | Set-ablation support | Pythia-410M L8H6 |
| 785 | R/C · Induction | linen *bag* … ⟦linen⟧ → bag | willow *basket* … ⟦willow⟧ → basket | Unknown exact payload | Set-ablation support | Pythia-410M L7H1 |
| 786 | R/C · Induction, also BOS | linen *bag* … ⟦linen⟧ → bag | willow *basket* … ⟦willow⟧ → basket | Unknown exact payload | Individual ablation hurts induction | Pythia-410M L11H14 |

### Tool-call state readout versus tool-format attention

Qwen3-8B, Appendix E, Tables 22–24; zero-based. First three rows highlight task cues only: their exact source routing is unresolved here. Last three show measured format-region preference. These readouts follow earlier state formation; none is established as the unique decision-maker. Attribution and patching effects differ, particularly for L33H11. [UT]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 787 | C · Earlier call readout | Tool schema; *execute the calculation* ⟦assistant boundary⟧ | Tool schema; *run the lookup* ⟦assistant boundary⟧ | Unknown exact payload | Patching can restore calling | Qwen3-8B L25H6 |
| 788 | C · Earlier call readout | Tool schema; *execute the calculation* ⟦assistant boundary⟧ | Tool schema; *run the lookup* ⟦assistant boundary⟧ | Unknown exact payload | Patching can restore calling | Qwen3-8B L28H3 |
| 789 | C · Earlier call readout | Tool schema; *execute the calculation* ⟦assistant boundary⟧ | Tool schema; *run the lookup* ⟦assistant boundary⟧ | Unknown exact payload | Patching can restore calling | Qwen3-8B L26H14 |
| 790 | R/C · Tool-format reader | *Tool-call format template* … Execute the sum. ⟦boundary⟧ | *Tool-call format template* … Run the lookup. ⟦boundary⟧ | Call-opening logit direction | Positive direct contribution; patch recovery | Qwen3-8B L29H9 |
| 791 | R/C · Late tool-format reader | *Tool-call format template* … Execute the sum. ⟦boundary⟧ | *Tool-call format template* … Run the lookup. ⟦boundary⟧ | Call-opening logit direction | Large direct contribution; limited patch recovery | Qwen3-8B L33H29 |
| 792 | R/C · Late tool-format reader | *Tool-call format template* … Execute the sum. ⟦boundary⟧ | *Tool-call format template* … Run the lookup. ⟦boundary⟧ | Call-opening logit direction | Positive attribution; no strict patch recovery | Qwen3-8B L33H11 |

### Propositional reasoning: locating rules, moving them, and selecting a proof

Appendices B.4–B.11; zero-based. **31 physical instances of shared roles**, not 31 algorithms. The answer starts with a premise variable, not “true/false.” Examples abbreviate the prompt; locators may also read adjacent punctuation. Fact attention is imperfect. Mistral L14H26 changes roles with query position. The final four examples mark sources without asserting an exact query position; operator-relay payloads remain hypotheses. [LR]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 793 | R/C · Locator | U or V implies *Q.* W implies Z. Query ⟦Q⟧ | M and N implies *R.* P implies S. Query ⟦R⟧ | Rule information; inferred | Upstream rule selection | Gemma-2-9B L19H11 |
| 794 | R/C · Locator | U or V implies *Q.* W implies Z. Query ⟦Q⟧ | M and N implies *R.* P implies S. Query ⟦R⟧ | Rule information; inferred | Upstream rule selection | Gemma-2-9B L21H7 |
| 795 | R/C · Locator | U or V implies *Q.* W implies Z. Query ⟦Q⟧ | M and N implies *R.* P implies S. Query ⟦R⟧ | Rule information; inferred | Upstream rule selection | Gemma-2-9B L22H5 |
| 796 | R/C · Locator | U or V implies *Q.* W implies Z. Query ⟦Q⟧ | M and N implies *R.* P implies S. Query ⟦R⟧ | Rule information; inferred | Upstream rule selection | Gemma-2-9B L23H12 |
| 797 | R/C · Mover | U or V implies Q; facts … Query *Q. Answer*⟦:⟧ | M and N implies R; facts … Query *R. Answer*⟦:⟧ | Rule information; inferred | Rule delivery to answer position | Gemma-2-9B L20H7 |
| 798 | R/C · Mover | U or V implies Q; facts … Query *Q. Answer*⟦:⟧ | M and N implies R; facts … Query *R. Answer*⟦:⟧ | Rule information; inferred | Rule delivery to answer position | Gemma-2-9B L23H6 |
| 799 | R/C · Mover | U or V implies Q; facts … Query *Q. Answer*⟦:⟧ | M and N implies R; facts … Query *R. Answer*⟦:⟧ | Rule information; inferred | Rule delivery to answer position | Gemma-2-9B L24H15 |
| 800 | R/C · Fact | U or V implies Q; *U is true. V is false.* Query Q. Answer⟦:⟧ | M and N implies R; *M is true. N is false.* Query R. Answer⟦:⟧ | Fact information; inferred | Supports decision stage | Gemma-2-9B L24H5 |
| 801 | R/C · Fact | U or V implies Q; *U is true. V is false.* Query Q. Answer⟦:⟧ | M and N implies R; *M is true. N is false.* Query R. Answer⟦:⟧ | Fact information; inferred | Supports decision stage | Gemma-2-9B L25H7 |
| 802 | R/C · Fact | U or V implies Q; *U is true. V is false.* Query Q. Answer⟦:⟧ | M and N implies R; *M is true. N is false.* Query R. Answer⟦:⟧ | Fact information; inferred | Supports decision stage | Gemma-2-9B L26H0 |
| 803 | R/C · Fact | U or V implies Q; *U is true. V is false.* Query Q. Answer⟦:⟧ | M and N implies R; *M is true. N is false.* Query R. Answer⟦:⟧ | Fact information; inferred | Supports decision stage | Gemma-2-9B L26H12 |
| 804 | R/C · Decision | *U* or V implies Q; *U* is true; V is false. Query Q. Answer⟦:⟧ → U | M and *N* implies R; M is true; *N* is false. Query R. Answer⟦:⟧ → N | Answer-variable evidence | Supports first proof token | Gemma-2-9B L28H12 |
| 805 | R/C · Decision | *U* or V implies Q; *U* is true; V is false. Query Q. Answer⟦:⟧ → U | M and *N* implies R; M is true; *N* is false. Query R. Answer⟦:⟧ → N | Answer-variable evidence | Supports first proof token | Gemma-2-9B L30H9 |
| 806 | R/C · Locator | U or V implies *Q.* W implies Z. Query ⟦Q⟧ | M and N implies *R.* P implies S. Query ⟦R⟧ | Rule information; inferred | Upstream rule selection | Mistral-7B L9H25 |
| 807 | R/C · Locator | U or V implies *Q.* W implies Z. Query ⟦Q⟧ | M and N implies *R.* P implies S. Query ⟦R⟧ | Rule information; inferred | Upstream rule selection | Mistral-7B L9H26 |
| 808 | R/C · Locator | U or V implies *Q.* W implies Z. Query ⟦Q⟧ | M and N implies *R.* P implies S. Query ⟦R⟧ | Rule information; inferred | Upstream rule selection | Mistral-7B L12H9 |
| 809 | R/C · Locator | U or V implies *Q.* W implies Z. Query ⟦Q⟧ | M and N implies *R.* P implies S. Query ⟦R⟧ | Rule information; inferred | Upstream rule selection | Mistral-7B L14H24 |
| 810 | R/C · Locator / fact reader | U or V implies *Q.* W implies Z. Query ⟦Q⟧ | M and N implies R; *M is true. N is false.* Query R. Answer⟦:⟧ | Position-dependent rule/fact signal | Supports both stages | Mistral-7B L14H26 |
| 811 | R/C · Mover | U or V implies Q; facts … Query *Q*. Answer⟦:⟧ | M and N implies R; facts … Query *R*. Answer⟦:⟧ | Rule information; inferred | Rule delivery to answer position | Mistral-7B L13H11 |
| 812 | R/C · Mover | U or V implies Q; facts … Query *Q*. Answer⟦:⟧ | M and N implies R; facts … Query *R*. Answer⟦:⟧ | Rule information; inferred | Rule delivery to answer position | Mistral-7B L13H22 |
| 813 | R/C · Mover — linear chain | U implies Q; U is true. Query *Q*. Answer⟦:⟧ | P implies R; P is false. Query *R*. Answer⟦:⟧ | Rule information; inferred | Conditional rule delivery | Mistral-7B L15H8 |
| 814 | R/C · Fact | U or V implies Q; *U is true. V is false.* Query Q. Answer⟦:⟧ | M and N implies R; *M is true. N is false.* Query R. Answer⟦:⟧ | Fact information; inferred | Supports decision stage | Mistral-7B L16H12 |
| 815 | R/C · Fact | U or V implies Q; *U is true. V is false.* Query Q. Answer⟦:⟧ | M and N implies R; *M is true. N is false.* Query R. Answer⟦:⟧ | Fact information; inferred | Supports decision stage | Mistral-7B L16H14 |
| 816 | R/C · Decision | *U* or V implies Q; *U* is true; V is false. Query Q. Answer⟦:⟧ → U | M and *N* implies R; M is true; *N* is false. Query R. Answer⟦:⟧ → N | Answer-variable evidence | Supports first proof token | Mistral-7B L19H8 |
| 817 | R/C · Decision | *U* or V implies Q; *U* is true; V is false. Query Q. Answer⟦:⟧ → U | M and *N* implies R; M is true; *N* is false. Query R. Answer⟦:⟧ → N | Answer-variable evidence | Supports first proof token | Mistral-7B L19H9 |
| 818 | R/C · Decision | *U* or V implies Q; *U* is true; V is false. Query Q. Answer⟦:⟧ → U | M and *N* implies R; M is true; *N* is false. Query R. Answer⟦:⟧ → N | Answer-variable evidence | Supports first proof token | Mistral-7B L19H16 |
| 819 | R/C · Decision — facts only | U or V implies Q; *U is true.* V is false. Query Q. Answer⟦:⟧ → U | M and N implies R; M is true. *N is false.* Query R. Answer⟦:⟧ → N | Answer-variable evidence | Supports first proof token | Mistral-7B L17H25 |
| 820 | R/C · Operator + facts | U *or* V implies Q; *U is true*; V is false; query Q | M *and* N implies R; M is true; *N is false*; query R | Operator/fact interaction; inferred | Affects decision heads | Gemma-2-27B L23H13 |
| 821 | R/C · Operator + facts | U *or* V implies Q; *U is true*; V is false; query Q | M *and* N implies R; M is true; *N is false*; query R | Operator/fact interaction; inferred | Affects decision heads | Gemma-2-27B L23H31 |
| 822 | R/C · Operator relay candidate | U *or* V implies Q; U=true, V=false; query Q | M *and* N implies R; M=true, N=false; query R | Operator signal; hypothesis | Influences later operator readers | Gemma-2-27B L20H16 |
| 823 | R/C · Operator relay candidate | U *or* V implies Q; U=true, V=false; query Q | M *and* N implies R; M=true, N=false; query R | Operator signal; hypothesis | Influences later operator readers | Gemma-2-27B L22H13 |

### Factual recall: relation signals and subject information

GPT-2 Medium, Figures 1–3 and §4. Labels are reproduced as reported. The detailed case concerns France/French; examples below are schematic analogues, not additional verified facts about these heads. Vocabulary readouts suggest payloads but do not fully decode them. The L7H14 signaling role is explicitly tentative. [KC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 824 | R/F · Relation reader | The official *language* of Spain ⟦is⟧ | The official *language* of Germany ⟦is⟧ | Language-category readout | Feeds MLP17 | GPT-2 Medium L14H13 |
| 825 | R/C · Subject-attribute extractor | The official language of *Spain* ⟦is⟧ → Spanish | The official language of *Germany* ⟦is⟧ → German | Answer-associated information | Supports factual answer | GPT-2 Medium L14H7 |
| 826 | R/F · Earlier relation reader | The official *language* of Spain ⟦is⟧ | The official *language* of Germany ⟦is⟧ | Language-token readout | Proposed signal to L14H7 | GPT-2 Medium L7H14 |
| 827 | R/F · Later relation reader | The official *language* of Spain ⟦is⟧ | The official *language* of Germany ⟦is⟧ | Unknown exact payload | Further answer enhancement | GPT-2 Medium L18H14 |
| 828 | R/F · Later subject reader | The official language of *Spain* ⟦is⟧ | The official language of *Germany* ⟦is⟧ | Unknown exact payload | Further answer enhancement | GPT-2 Medium L20H6 |

### Natural-text routing: acronym, place, noun phrase, and noun preference

GPT-2 Small, §5.3 and Tables 1–3; zero-based. Routing was observed; suggested prediction functions were not causally established. L9H0's noun preference is aggregate, so its examples mark candidate sources, not a precise deterministic route. L11H2 adds routing evidence to the earlier weight-association entry 387. [VB]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 829 | R · Acronym fragment → phrase | Cedar *River* Association (⟦C⟧ → R | Birch *Lake* Society (⟦B⟧ → L | Unknown | Acronym continuation; hypothesis | GPT-2 Small L10H10 |
| 830 | R · Comma → place | *Oslo*⟦,⟧ → Norway | *Kyoto*⟦,⟧ → Japan | Unknown | Related place continuation; hypothesis | GPT-2 Small L11H2 |
| 831 | R · Phrase end → head noun | The *lanterns* beside the old ⟦gate⟧ → were | The *boat* near the wooden ⟦pier⟧ → was | Unknown | Following verb prediction; hypothesis | GPT-2 Small L11H10 |
| 832 | R · Noun preference | The *carpenter* stacked *planks* ⟦carefully⟧ | A *child* carried a *basket* ⟦outside⟧ | Unknown | Unknown | GPT-2 Small L9H0 |

### Contrastive sentiment: same source word, different output effects

Sections 6.2–6.4 and Appendix C.4; zero-based. “Substitution” changes a sentiment word; “negation” can preserve it after “not.” The last row is a **conditional behavior of L10H1**, not an extra physical head. Payload labels summarize circuit/readout evidence. GPT-2 L10H7's sentiment role also complements its copy-suppression role in entry 9. [CS]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 833 | R/C · Target-label relay | Positive: The soup is tasty. *Negative*: The soup ⟦is⟧ | Negative: The room is ugly. *Positive*: The room ⟦is⟧ | Target sentiment | Supports substitution through MLPs | GPT-2 Small L7H5 |
| 834 | R/F · Valenced-word reader | Positive: The soup is *tasty*. Negative: The soup ⟦is⟧ | Negative: The room is *ugly*. Positive: The room ⟦is⟧ | Word-related information | Supports substitution | GPT-2 Small L9H7 |
| 835 | R/F · Valenced-word reader | Positive: The soup is *tasty*. Negative: The soup ⟦is⟧ | Negative: The room is *ugly*. Positive: The room ⟦is⟧ | Word-related information | Supports substitution | GPT-2 Small L10H7 |
| 836 | R/C · Word preservation | Positive: The soup is *tasty*. Negative: The soup ⟦is⟧ | Negative: The room is *ugly*. Positive: The room ⟦is⟧ | Original-word evidence | Opposes substitution | GPT-2 Small L10H1 |
| 837 | R/F · Word preservation | Positive: The soup is *tasty*. Negative: The soup ⟦is⟧ | Negative: The room is *ugly*. Positive: The room ⟦is⟧ | Original-word evidence | Opposes substitution | GPT-2 Small L10H4 |
| 838 | R/C · Target-label relay | Positive: The soup is tasty. *Negative*: The soup ⟦is⟧ | Negative: The room is ugly. *Positive*: The room ⟦is⟧ | Target sentiment | Amplification improves flipping | Pythia-410M L13H10 |
| 839 | R/C · Word preservation | Positive: The soup is *tasty*. Negative: The soup ⟦is⟧ | Negative: The room is *ugly*. Positive: The room ⟦is⟧ | Original-word evidence | Suppression improves substitution | Pythia-410M L17H9 |
| 840 | R/F · Preservation after negation | Positive: The soup is *tasty*. Negative: The soup is ⟦not⟧ → tasty | Negative: The room is *ugly*. Positive: The room is ⟦not⟧ → ugly | Original-word evidence | Supports negated completion | GPT-2 Small L10H1; negation |

## Additional researched entries: 841–940

This batch adds physical head instances, task-conditioned behaviors, and explicitly named families. They are not 100 distinct algorithms. R = observed routing; C = causal evidence at the stated scope; F = association/readout evidence; T = trained toy model. All examples are illustrative.

### Temporal ordering: relational words, punctuation, and event spans

Appendices B–C, Figures 14–25; reported zero-based IDs. C denotes path-patching evidence; its sign is not a universal helpful/harmful classification. Attention modulation affects heads differently. [TO]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 841 | R/C · Question-mark reader | Nia packed, then left. Was packing before leaving *?* Answer⟦:⟧ | Omar ate, then rested. Was resting after eating *?* Answer⟦:⟧ | Unknown | Temporal-answer sensitivity | LLaMA2-7B L13H4 |
| 842 | R/C · Question-mark reader | Nia packed, then left. Was packing before leaving *?* Answer⟦:⟧ | Omar ate, then rested. Was resting after eating *?* Answer⟦:⟧ | Unknown | Temporal-answer sensitivity | LLaMA2-7B L15H31 |
| 843 | R/C · Question-mark reader | Nia packed, then left. Was packing before leaving *?* Answer⟦:⟧ | Omar ate, then rested. Was resting after eating *?* Answer⟦:⟧ | Unknown | Temporal-answer sensitivity | LLaMA2-7B L16H0 |
| 844 | R/C · Question-mark reader | Nia packed, then left. Was packing before leaving *?* Answer⟦:⟧ | Omar ate, then rested. Was resting after eating *?* Answer⟦:⟧ | Unknown | Temporal-answer sensitivity | LLaMA2-7B L16H15 |
| 845 | R/C · Question-mark reader | Nia packed, then left. Was packing before leaving *?* Answer⟦:⟧ | Omar ate, then rested. Was resting after eating *?* Answer⟦:⟧ | Unknown | Temporal-answer sensitivity | LLaMA2-7B L27H7 |
| 846 | R/C · Temporal-word reader | Nia packed, then left. Was packing *before* leaving? Answer⟦:⟧ | Omar ate, then rested. Was resting *after* eating? Answer⟦:⟧ | Unknown | Temporal-answer sensitivity | LLaMA2-7B L17H31 |
| 847 | R/C · Temporal-word reader; also BOS | Nia packed, then left. Was packing *before* leaving? Answer⟦:⟧ | Omar ate, then rested. Was resting *after* eating? Answer⟦:⟧ | Unknown | Temporal-answer sensitivity | LLaMA2-7B L19H19 |
| 848 | R · Article-event reader | Nia *packed*, then left. Was packing before leaving? Answer⟦:⟧ | Omar *ate*, then rested. Was eating before resting? Answer⟦:⟧ | Unknown | Low patch effect | LLaMA2-7B L10H14 |
| 849 | R · Question-event reader | Nia packed, then left. Was *packing* before leaving? Answer⟦:⟧ | Omar ate, then rested. Was *eating* before resting? Answer⟦:⟧ | Unknown | Low patch effect | LLaMA2-7B L13H22 |
| 850 | R/C · Temporal reader | Nia packed, then left. Was packing *before* leaving? Answer⟦:⟧ | Omar ate, then rested. Was resting *after* eating? Answer⟦:⟧ | Unknown | Temporal-answer sensitivity | LLaMA3-8B L14H5 |
| 851 | R/C · Structural reader | Nia packed, then left. Was packing before leaving *?* Answer⟦:⟧ | Omar ate, then rested. Was resting after eating *?* Answer⟦:⟧ | Unknown | Temporal-answer sensitivity | LLaMA3-8B L14H7 |
| 852 | R/C · Temporal reader | Nia packed, then left. Was packing *before* leaving? Answer⟦:⟧ | Omar ate, then rested. Was resting *after* eating? Answer⟦:⟧ | Unknown | Temporal-answer sensitivity | Qwen2-7B L19H23 |
| 853 | R/C · Structural reader | Nia packed, then left. Was packing before leaving *?* Answer⟦:⟧ | Omar ate, then rested. Was resting after eating *?* Answer⟦:⟧ | Unknown | Temporal-answer sensitivity | Qwen2-7B L20H3 |

### Filtering a collection using a portable predicate

Appendix N's 16 strongest positive individual query-patch effects; IDs as reported. Illustrations show family-level selection, directly visualized for L35H19, not 16 measured traces. Predicate information is in Q. Collective OV patching suggests content and position signals, but leaves individual payloads unresolved. [FI]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 854 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +3.546 | Llama-70B L35H19 |
| 855 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +1.353 | Llama-70B L39H45 |
| 856 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +1.306 | Llama-70B L35H17 |
| 857 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +1.114 | Llama-70B L31H38 |
| 858 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.611 | Llama-70B L35H40 |
| 859 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.443 | Llama-70B L35H20 |
| 860 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.341 | Llama-70B L31H39 |
| 861 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.282 | Llama-70B L35H18 |
| 862 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.209 | Llama-70B L29H56 |
| 863 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.155 | Llama-70B L42H31 |
| 864 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.152 | Llama-70B L28H40 |
| 865 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.141 | Llama-70B L29H61 |
| 866 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.129 | Llama-70B L36H47 |
| 867 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.110 | Llama-70B L34H6 |
| 868 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.106 | Llama-70B L37H30 |
| 869 | C · Predicate filter | hammer, *pear*, truck; choose fruit⟦:⟧ → pear | tulip, *canoe*, wool; choose vehicle⟦:⟧ → canoe | Individually unresolved | Query-patch AIE +0.104 | Llama-70B L35H23 |

### Abstract symbols and concrete tokens: identity-rule tasks

Sections 2–3, Llama-3.1-70B. These are three head families, not three assigned physical IDs. Routing and representational/causal analyses distinguish their roles. [AB]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 870 | R/C · Symbol abstraction | *cedar* ^ moss ^ ⟦cedar⟧ | cedar ^ *moss* ^ ⟦moss⟧ | Abstract role | Encodes A/B identity | Early-layer family |
| 871 | R/C · Symbolic induction | cedar ^ moss ^ *cedar*; lime ^ rose ⟦^⟧ → lime | cedar ^ moss ^ *moss*; lime ^ rose ⟦^⟧ → rose | Predicted role | Supports rule continuation | Intermediate-layer family |
| 872 | R/C · Value retrieval | cedar ^ moss ^ cedar; *lime* ^ rose ⟦^⟧ → lime | cedar ^ moss ^ moss; lime ^ *rose* ⟦^⟧ → rose | Token identity | Instantiates predicted role | Later-layer family |

### Analogy tasks: task-conditioned symbolic roles

Appendix C.5, Llama-3.1-70B. Eight task/role families, potentially overlapping; no individual IDs assigned. Here italics mark task cues, not verified attention sources. Patching positions are identified separately from routing. Payloads are role-level interpretations. [AB]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 873 | C · Letter-rule abstraction | [d e f] → [d e *g*] | [j k l] → [*i* k l] | Relation information | Supports analogy | Early family |
| 874 | C · Letter-rule induction | [d e f] → [d e *g*]; [m n o] → […] | [j k l] → [*i* k l]; [r s t] → […] | Selected relation | Controls transformation | Intermediate family |
| 875 | C · Letter-value retrieval | [d e f] → [d e g]; [m n *o*] → [m n …] | [j k l] → [i k l]; [*r* s t] → […] | Letter information | Feeds transformation downstream | Later family |
| 876 | C · Antonym abstraction | cold: *hot*; narrow: wide; quiet: … | dry: *wet*; early: late; clean: … | Relation information | Supports antonymy | Early family |
| 877 | C · Synonym abstraction | tiny: *small*; quick: fast; silent: … | glad: *happy*; ill: sick; large: … | Relation information | Supports synonymy | Early family |
| 878 | C · Antonym induction | *cold: hot*; narrow: wide; quiet: … | *dry: wet*; early: late; clean: … | Selected relation | Controls antonym answer | Intermediate family |
| 879 | C · Synonym induction | *tiny: small*; quick: fast; silent: … | *glad: happy*; ill: sick; large: … | Selected relation | Controls synonym answer | Intermediate family |
| 880 | C · Lexical retrieval | cold: hot; narrow: wide; *quiet*: … | tiny: small; quick: fast; *silent*: … | Lexical information | Supports word selection | Later family; pooled relations |

### Molecular graphs: chemical substructures and a dummy node

Appendix G, Table 19. I–VI are the authors' pattern labels, not numerical head IDs. Italics show preferred atoms under column-averaged attention; no particular query atom is established. The learned attention term coexists with graph and distance terms. [MA]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 881 | R · Unsubstituted aromatic carbon | benzene: *ring carbon* | toluene: *unsubstituted ring carbon* | Unknown | Unknown | MAT first layer; I |
| 882 | R · Sulfur | ethanethiol: *S* | dimethyl sulfide: *S* | Unknown | Unknown | MAT first layer; II |
| 883 | R · Non-ring nitrogen | ethylamine: *N* | acetamide: *N* | Unknown | Unknown | MAT first layer; III |
| 884 | R · Carbonyl oxygen | acetone: C=*O* | acetaldehyde: C=*O* | Unknown | Unknown | MAT first layer; IV |
| 885 | R · Aromatic substitution site | anisole: *ring carbon bonded to O* | toluene: *ring carbon bonded to methyl* | Unknown | Unknown | MAT first layer; V; also sulfur-sensitive |
| 886 | R · Aromatic nitrogen | pyridine: *ring N* | pyrimidine: *ring N* | Unknown | Unknown | MAT first layer; VI |
| 887 | R · Dummy-node preference | ethanol atoms + *dummy* | benzene atoms + *dummy* | Unknown | Possible no-op; hypothesis | MAT family; index unstated |

### Molecular strings: ring pointers, writers, and branches

Table 1, zero-based. Ring-pointer and writer roles are functionally distinct; L2 cannot feed L1 in the same pass. Writer examples mark task cues only. Ablation percentages are generation validity, not accuracy of the illustrative strings. [MG]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 888 | R/C · Ring-opener pointer | C *1* C C C C C ⟦1⟧ | C *1* C C O C ⟦1⟧ | Unresolved | Ablated validity 79.6% | 25M molecular model L2H7 |
| 889 | C · Ring-closure writer | C *1* C C C C C 1 | C *1* C C O C 1 | Unresolved | Ablated validity 25.4% | 25M molecular model L1H2 |
| 890 | R/C · Branch-opener pointer | C C *(* C ⟦)⟧ O | C C *(* O ⟦)⟧ C | Unresolved | Ablated validity 63.7% | 25M molecular model L2H3 |

### A reused molecular head: computation across passes

Section 4.3, Table 3. Two model instances, not extra heads per pass. Italics are bracket cues; routing and output encoding were not decoded. Paper pass numbers start at 1; the bracket-head index varies with seed (H2 for s42, H1 for s43). [SM]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 891 | C · Bracket matching | C C *(* C *)* O | C C C *(* O *)* C | Unknown | Selective errors after pass 1–3 ablation | SMolLM WS-53K shared block; H2/H1 by seed |
| 892 | C · Bracket matching | C C *(* C *)* O | C C C *(* O *)* C | Unknown | Strongest dependence on early passes | SMolLM WS-206K shared block; H2/H1 by seed |

### Counting through intermediate answers

Sections 4–5; Qwen2.5-7B, reported IDs. Source-token count representations have probing evidence; exact head-output encodings remain inferred. The intermediate-count example marks an already-generated count token, not its preceding prediction position. [CN]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 893 | R/C · Partition-count transfer | plum, plum *, plum*; part 1: ⟦3⟧ | pear, pear, pear *, pear*; part 1: ⟦4⟧ | Local count; inferred | Supports intermediate steps | Qwen2.5-7B L22H13 |
| 894 | R/C · Count aggregation | part 1: *3*; part 2: *4*; total⟦:⟧ → 7 | part 1: *5*; part 2: *3*; total⟦:⟧ → 8 | Intermediate counts; inferred | Supports final total | Qwen2.5-7B L22H1 |

### Negation in a contrastive text encoder

Figures 4, 6–7. Preserve the paper's one-based layer/head labels. These are observed negator preferences; they do not establish reliable negation understanding or individual-head causal effects. The second row has no specified query position. [CL]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 895 | R · Negator → sentence end | There are *no* boats⟦.⟧ EOT | There is *no* ladder⟦.⟧ EOT | Unknown | Unknown | CLIP text encoder L4H2 |
| 896 | R · Negator preference | The gate is *not* open. | She did *not* wait. | Unknown | Unknown | CLIP text encoder L2H1; CANNOT |

### Belief tracking: three lookback circuit families

Sections 4–6; Llama-3-70B-Instruct. C applies to subspaces/circuits, not separately validated physical heads. Illustrations simplify the pointer/address mechanism. Visibility payload semantics remain uncertain in the two-character setting. [BL]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 897 | C · Binding lookback | Mira fills cup with *milk*. Belief of Mira about cup⟦?⟧ | Omar fills box with *sand*. Belief of Omar about box⟦?⟧ | State ordering ID | Selects answer reference | Family; head IDs not assigned |
| 898 | C · Answer lookback | Mira fills cup with *milk*. Belief of Mira about cup⟦?⟧ → milk | Omar fills box with *sand*. Belief of Omar about box⟦?⟧ → sand | State-token value | Resolves answer reference | Family; head IDs not assigned |
| 899 | C · Visibility lookback | Theo fills opaque jar with juice. *Mira sees Theo*. Mira's belief⟦?⟧ | Nia fills opaque bucket with pebbles. *Omar sees Nia*. Omar's belief⟦?⟧ | Observed-character ID; tentative | Updates accessible knowledge | Family; head IDs not assigned |

### Acoustic time series: preferred source frames

Section 5; zero-based. Italics mark late source frames under query-averaged attention. Output patching is a different measurement: it identifies influential destination activations. Evidence is from the studied clean/corrupt same-speaker pair, not all audio. [TI]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 900 | R/C · Late-frame preference | utterance A: frames 0…*late frames* | utterance B: frames 0…*late frames* | Unknown | Patching improves speaker confidence | JapaneseVowels transformer L0H6 |

### Multiple choice: reading selection before the final answer

Tables 7–8 list 17 unique high-ranking heads across datasets/shots. Pre-RoPE QK scores compare the final query with option-ending newlines (↵); this is a predictive readout, not proof of each head's downstream effect. Examples show the candidate family route. Figure 6 directly illustrates L17H26. [QK]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 901 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-3.1-8B L16H19 |
| 902 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-3.1-8B L17H24 |
| 903 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-3.1-8B L16H26 |
| 904 | R/F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-3.1-8B L17H26 |
| 905 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-3.1-8B L14H5 |
| 906 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-3.1-8B L14H21 |
| 907 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-3.1-8B L14H2 |
| 908 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-3.1-8B L17H29 |
| 909 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-2-7B L14H24 |
| 910 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-2-7B L15H4 |
| 911 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-2-7B L17H0 |
| 912 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-2-7B L14H20 |
| 913 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-2-7B L14H29 |
| 914 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-2-7B L14H26 |
| 915 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-2-7B L15H5 |
| 916 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-2-7B L18H10 |
| 917 | F · Option-end selector | Which grows? A. stone ↵ B. fern *↵* Answer⟦:⟧ | Which floats? A. cork *↵* B. brick ↵ Answer⟦:⟧ | Unknown | Unknown | LLaMA-2-7B L15H23 |

### Two copying routes: next token versus the end of a word

Figure 3b and §§2–4; zero-based. Six physical instances of two roles. Illustrative subword splits (·) are schematic. Causal scores distinguish next-token from next-next-token information; task-level ablations concern head sets. [DI]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 918 | R/C · Token-level copying | beside the *candle*·stick … beside ⟦the⟧ → candle | near the *light*·house … near ⟦the⟧ → light | Next-token evidence | Supports verbatim copying | Llama-2-7B L16H19 |
| 919 | R/C · Token-level copying | beside the *candle*·stick … beside ⟦the⟧ → candle | near the *light*·house … near ⟦the⟧ → light | Next-token evidence | Supports verbatim copying | Llama-2-7B L11H15 |
| 920 | R/C · Token-level copying | beside the *candle*·stick … beside ⟦the⟧ → candle | near the *light*·house … near ⟦the⟧ → light | Next-token evidence | Supports verbatim copying | Llama-2-7B L12H26 |
| 921 | R/C · Concept-level copying | beside the candle·*stick* … beside ⟦the⟧ → candle | near the light·*house* … near ⟦the⟧ → light | Whole-word information; inferred | Supports semantic copying | Llama-2-7B L13H23 |
| 922 | R/C · Concept-level copying | beside the candle·*stick* … beside ⟦the⟧ → candle | near the light·*house* … near ⟦the⟧ → light | Whole-word information; inferred | Supports semantic copying | Llama-2-7B L14H7 |
| 923 | R/C · Concept-level copying | beside the candle·*stick* … beside ⟦the⟧ → candle | near the light·*house* … near ⟦the⟧ → light | Whole-word information; inferred | Supports semantic copying | Llama-2-7B L10H14 |

### A two-layer arithmetic model: constructing and following bindings

Section 5, Figures 5–7. Three conditional behaviors of only two physical heads. Paper layers are 1-based; each layer has one head. Padding omitted; the paper places + before operands and performs addition modulo 59. [AA]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 924 | T/R · Variable → assigned constant | *a* ⟦8⟧ b 11 … + a b = | a 4 *b* ⟦9⟧ … + a b = | Remapped variable embedding | Builds matching address | Layer 1; assignment positions |
| 925 | T/R · Operands → equals | a 8 b 11 … + *a* *b* ⟦=⟧ | a 4 b 9 … + *a* *b* ⟦=⟧ | Remapped operand embeddings | Builds lookup query | Layer 1; equals position |
| 926 | T/R · Binding dereference | a *8* b *11* … + a b ⟦=⟧ → 19 | a *4* b *9* … + a b ⟦=⟧ → 13 | Assigned numeric operands | Feeds addition MLP | Layer 2; equals position |

### Deduction: reading rules, choosing premises, and traversal control

Figure 3 and §4.2; zero-based. Causal span/path patching establishes roles, not token-routing maps: italics are task cues. Fourteen physical instances; roles can overlap. Matching labels use the figure's coordinates (L13H4), not the prose's inconsistent L11H4. [DC]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 927 | C · Rule/fact reader | Facts: *P*. Rule 1: *P ⇒ Q*. Derive Q. | Facts: *R*. Rule 2: *R ⇒ S*. Derive S. | Task information | Supports deduction | Llama-3.1-8B-Instruct L10H1 |
| 928 | C · Rule/fact reader | Facts: *P*. Rule 1: *P ⇒ Q*. Derive Q. | Facts: *R*. Rule 2: *R ⇒ S*. Derive S. | Task information | Supports deduction | Llama-3.1-8B-Instruct L10H2 |
| 929 | C · Rule/fact reader | Facts: *P*. Rule 1: *P ⇒ Q*. Derive Q. | Facts: *R*. Rule 2: *R ⇒ S*. Derive S. | Task information | Supports deduction | Llama-3.1-8B-Instruct L11H12 |
| 930 | C · Condition matching | Facts: P, R. Rule: *P ∧ R* ⇒ Q. | Facts: S, T. Rule: *S ∧ T* ⇒ U. | Unresolved | Premise termination | Llama-3.1-8B-Instruct L13H4 |
| 931 | C · Condition matching | Facts: P, R. Rule: *P ∧ R* ⇒ Q. | Facts: S, T. Rule: *S ∧ T* ⇒ U. | Unresolved | Premise termination | Llama-3.1-8B-Instruct L15H8 |
| 932 | C · Condition matching | Facts: P, R. Rule: *P ∧ R* ⇒ Q. | Facts: S, T. Rule: *S ∧ T* ⇒ U. | Unresolved | Premise termination | Llama-3.1-8B-Instruct L19H12 |
| 933 | C · Rule selection | Facts: P. *Rule 1: P ⇒ Q*. Select rule: … | Facts: R. *Rule 2: R ⇒ S*. Select rule: … | Unresolved | Rule choice | Llama-3.1-8B-Instruct L17H24 |
| 934 | C · Rule selection | Facts: P. *Rule 1: P ⇒ Q*. Select rule: … | Facts: R. *Rule 2: R ⇒ S*. Select rule: … | Unresolved | Rule choice | Llama-3.1-8B-Instruct L17H25 |
| 935 | C · Rule selection | Facts: P. *Rule 1: P ⇒ Q*. Select rule: … | Facts: R. *Rule 2: R ⇒ S*. Select rule: … | Unresolved | Rule choice | Llama-3.1-8B-Instruct L28H18 |
| 936 | C · Premise selection | Facts: *P*, R. Rule: P ⇒ Q. Select premise: … | Facts: *S*, T. Rule: S ⇒ U. Select premise: … | Unresolved | Premise choice | Llama-3.1-8B-Instruct L18H23 |
| 937 | C · Premise selection | Facts: *P*, R. Rule: P ⇒ Q. Select premise: … | Facts: *S*, T. Rule: S ⇒ U. Select premise: … | Unresolved | Premise choice | Llama-3.1-8B-Instruct L18H28 |
| 938 | C · Premise selection | Facts: *P*, R. Rule: P ⇒ Q. Select premise: … | Facts: *S*, T. Rule: S ⇒ U. Select premise: … | Unresolved | Premise choice | Llama-3.1-8B-Instruct L30H26 |
| 939 | C · Traversal control | Demo: *P → Q, P → R, Q → S*. New graph: … | Demo: *A → B, A → C, B → D*. New graph: … | Unresolved | Traversal order | Llama-3.1-8B-Instruct L16H29 |
| 940 | C · Traversal control | Demo: *P → Q, P → R, Q → S*. New graph: … | Demo: *A → B, A → C, B → D*. New graph: … | Unresolved | Traversal order | Llama-3.1-8B-Instruct L21H10 |

## Final researched expansion: entries 941–1024

Added 2026-11-05 from eight further primary sources. This batch reaches the 1,024-entry target. It includes physical head instances, repeated mechanisms across checkpoints, and explicitly labeled families. Examples remain illustrative.

### TinySQL: table-name associations across three checkpoints

**F.** Table 11's CS1/CS2/CS3 evaluations identify SAE associations with table-name generation. Italics mark schema cues, **not measured routing**. These are 24 physical instances in three separately trained checkpoints, not 24 algorithms; individual payloads and causal effects remain unresolved. Indices are zero-based. [SQ]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 941 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees. SELECT tree FROM … | Schema: *harbor*(boat, berth). List boats. SELECT boat FROM … | Unknown | Unknown | BM1_CS1_Syn L0H1 |
| 942 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees. SELECT tree FROM … | Schema: *harbor*(boat, berth). List boats. SELECT boat FROM … | Unknown | Unknown | BM1_CS1_Syn L0H10 |
| 943 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees. SELECT tree FROM … | Schema: *harbor*(boat, berth). List boats. SELECT boat FROM … | Unknown | Unknown | BM1_CS1_Syn L0H8 |
| 944 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees. SELECT tree FROM … | Schema: *harbor*(boat, berth). List boats. SELECT boat FROM … | Unknown | Unknown | BM1_CS1_Syn L0H7 |
| 945 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees. SELECT tree FROM … | Schema: *harbor*(boat, berth). List boats. SELECT boat FROM … | Unknown | Unknown | BM1_CS1_Syn L1H13 |
| 946 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees. SELECT tree FROM … | Schema: *harbor*(boat, berth). List boats. SELECT boat FROM … | Unknown | Unknown | BM1_CS1_Syn L1H4 |
| 947 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees. SELECT tree FROM … | Schema: *harbor*(boat, berth). List boats. SELECT boat FROM … | Unknown | Unknown | BM1_CS1_Syn L1H1 |
| 948 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees. SELECT tree FROM … | Schema: *harbor*(boat, berth). List boats. SELECT boat FROM … | Unknown | Unknown | BM1_CS1_Syn L1H12 |
| 949 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees oldest first. SELECT tree FROM … ORDER BY age DESC | Schema: *harbor*(boat, berth). List boats by berth. SELECT boat FROM … ORDER BY berth | Unknown | Unknown | BM1_CS2_Syn L0H1 |
| 950 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees oldest first. SELECT tree FROM … ORDER BY age DESC | Schema: *harbor*(boat, berth). List boats by berth. SELECT boat FROM … ORDER BY berth | Unknown | Unknown | BM1_CS2_Syn L0H10 |
| 951 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees oldest first. SELECT tree FROM … ORDER BY age DESC | Schema: *harbor*(boat, berth). List boats by berth. SELECT boat FROM … ORDER BY berth | Unknown | Unknown | BM1_CS2_Syn L0H8 |
| 952 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees oldest first. SELECT tree FROM … ORDER BY age DESC | Schema: *harbor*(boat, berth). List boats by berth. SELECT boat FROM … ORDER BY berth | Unknown | Unknown | BM1_CS2_Syn L0H14 |
| 953 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees oldest first. SELECT tree FROM … ORDER BY age DESC | Schema: *harbor*(boat, berth). List boats by berth. SELECT boat FROM … ORDER BY berth | Unknown | Unknown | BM1_CS2_Syn L1H13 |
| 954 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees oldest first. SELECT tree FROM … ORDER BY age DESC | Schema: *harbor*(boat, berth). List boats by berth. SELECT boat FROM … ORDER BY berth | Unknown | Unknown | BM1_CS2_Syn L1H8 |
| 955 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees oldest first. SELECT tree FROM … ORDER BY age DESC | Schema: *harbor*(boat, berth). List boats by berth. SELECT boat FROM … ORDER BY berth | Unknown | Unknown | BM1_CS2_Syn L1H4 |
| 956 | Table-name [SQ] | Schema: *orchard*(tree, age). List trees oldest first. SELECT tree FROM … ORDER BY age DESC | Schema: *harbor*(boat, berth). List boats by berth. SELECT boat FROM … ORDER BY berth | Unknown | Unknown | BM1_CS2_Syn L1H1 |
| 957 | Table-name [SQ] | Schema: *orchard*(variety, age). Count trees per variety. SELECT variety, COUNT(1) FROM … GROUP BY variety | Schema: *harbor*(boat, berth). Count boats per berth. SELECT berth, COUNT(1) FROM … GROUP BY berth | Unknown | Unknown | BM1_CS3_Syn L0H1 |
| 958 | Table-name [SQ] | Schema: *orchard*(variety, age). Count trees per variety. SELECT variety, COUNT(1) FROM … GROUP BY variety | Schema: *harbor*(boat, berth). Count boats per berth. SELECT berth, COUNT(1) FROM … GROUP BY berth | Unknown | Unknown | BM1_CS3_Syn L0H10 |
| 959 | Table-name [SQ] | Schema: *orchard*(variety, age). Count trees per variety. SELECT variety, COUNT(1) FROM … GROUP BY variety | Schema: *harbor*(boat, berth). Count boats per berth. SELECT berth, COUNT(1) FROM … GROUP BY berth | Unknown | Unknown | BM1_CS3_Syn L0H8 |
| 960 | Table-name [SQ] | Schema: *orchard*(variety, age). Count trees per variety. SELECT variety, COUNT(1) FROM … GROUP BY variety | Schema: *harbor*(boat, berth). Count boats per berth. SELECT berth, COUNT(1) FROM … GROUP BY berth | Unknown | Unknown | BM1_CS3_Syn L0H14 |
| 961 | Table-name [SQ] | Schema: *orchard*(variety, age). Count trees per variety. SELECT variety, COUNT(1) FROM … GROUP BY variety | Schema: *harbor*(boat, berth). Count boats per berth. SELECT berth, COUNT(1) FROM … GROUP BY berth | Unknown | Unknown | BM1_CS3_Syn L1H6 |
| 962 | Table-name [SQ] | Schema: *orchard*(variety, age). Count trees per variety. SELECT variety, COUNT(1) FROM … GROUP BY variety | Schema: *harbor*(boat, berth). Count boats per berth. SELECT berth, COUNT(1) FROM … GROUP BY berth | Unknown | Unknown | BM1_CS3_Syn L1H2 |
| 963 | Table-name [SQ] | Schema: *orchard*(variety, age). Count trees per variety. SELECT variety, COUNT(1) FROM … GROUP BY variety | Schema: *harbor*(boat, berth). Count boats per berth. SELECT berth, COUNT(1) FROM … GROUP BY berth | Unknown | Unknown | BM1_CS3_Syn L1H1 |
| 964 | Table-name [SQ] | Schema: *orchard*(variety, age). Count trees per variety. SELECT variety, COUNT(1) FROM … GROUP BY variety | Schema: *harbor*(boat, berth). Count boats per berth. SELECT berth, COUNT(1) FROM … GROUP BY berth | Unknown | Unknown | BM1_CS3_Syn L1H13 |

### Head Pursuit: output-direction specialization

**F/C.** Italics mark feature cues, not attention targets. The first four entries use Table 1's output-direction associations in Mistral-7B-Instruct-v0.2; their individual causal effects are unknown. Remaining entries are selected head **families**: intervention results concern sets. Visual families use LLaVA-NeXT-7B (llava-v1.6-mistral-7b-hf). [HP]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 965 | Politics [HP] | The debate concerned *parliament*. | The report mentioned an *election*. | Politics-associated directions | Unknown | Mistral L18H27 |
| 966 | Nationality [HP] | Her passport is *Canadian*. | The athlete is *Brazilian*. | Nationality-associated directions | Unknown | Mistral L24H20 |
| 967 | Months [HP] | The festival starts in *April*. | The harbor freezes in *December*. | Month-associated directions | Unknown | Mistral L25H14 |
| 968 | Numbers [HP] | The crate held *seventeen* pieces. | The station opened in *1982*. | Number-associated directions | Unknown | Mistral L30H28 |
| 969 | Toxic-language family [HP] | You are an *idiot*. | That was *stupid*. | Dictionary-selected outputs | Sign inversion reduces toxicity | Mistral; family |
| 970 | Color family [HP] | Image: a *red coat* beside a tree. | Image: a *blue boat* on water. | Color-associated outputs | Modulates color mentions | LLaVA; family |
| 971 | Sentiment family [HP] | Image: a *smiling child*. | Image: an *angry face*. | Sentiment-associated outputs | Modulates sentiment mentions | LLaVA; family |
| 972 | Quantity family [HP] | Image: *three cups* on a shelf. | Image: *two dogs* on grass. | Quantity-associated outputs | Modulates quantity mentions | LLaVA; family |

### Trained regression heads: similarity, subtraction, and superposition

**T/R.** Separate one-layer models; head numbers are one-based. Scores illustrate query–example dot products; s₁/s₂ restrict them to task-specific coordinates, with other coordinates zero. Here μ>0 denotes magnitude; weighted-score uses coefficient magnitudes before polarity. Opposite-sign heads jointly approximate debiased gradient descent; no single head implements the entire predictor. Three-head models share tasks. Figures 2, 18–19 and Table 2. [RG]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 973 | Negative similarity [RG] | ⟦q⟧; score: A=+2, *B=−2* | ⟦q⟧; score: *A=−1*, B=+1 | −μy | Regression contribution | 2-head/1-task H1 |
| 974 | Positive similarity [RG] | ⟦q⟧; score: *A=+2*, B=−2 | ⟦q⟧; score: A=−1, *B=+1* | +μy | Regression contribution | 2-head/1-task H2 |
| 975 | Negative similarity [RG] | ⟦q⟧; score: A=+2, *B=−2* | ⟦q⟧; score: *A=−1*, B=+1 | −μy | Regression contribution | 4-head/1-task H1 |
| 976 | Positive similarity [RG] | ⟦q⟧; score: *A=+2*, B=−2 | ⟦q⟧; score: A=−1, *B=+1* | +μy | Regression contribution | 4-head/1-task H2 |
| 977 | Negative similarity [RG] | ⟦q⟧; score: A=+2, *B=−2* | ⟦q⟧; score: *A=−1*, B=+1 | −μy | Regression contribution | 4-head/1-task H3 |
| 978 | Dummy [RG] | ⟦q⟧ reads *A, B* nearly equally. | ⟦q⟧ reads *C, D* nearly equally. | Near-zero | Near-zero contribution | 4-head/1-task H4 |
| 979 | Positive s₁ [RG] | ⟦q⟧; s₁: *A=+2*, B=−2 | ⟦q⟧; s₁: A=−1, *B=+1* | +μy | Regression contribution | 4-head/2-task H1 |
| 980 | Negative s₁ [RG] | ⟦q⟧; s₁: A=+2, *B=−2* | ⟦q⟧; s₁: *A=−1*, B=+1 | −μy | Regression contribution | 4-head/2-task H2 |
| 981 | Positive s₂ [RG] | ⟦q⟧; s₂: *A=+2*, B=−2 | ⟦q⟧; s₂: A=−1, *B=+1* | +μy | Regression contribution | 4-head/2-task H3 |
| 982 | Negative s₂ [RG] | ⟦q⟧; s₂: A=+2, *B=−2* | ⟦q⟧; s₂: *A=−1*, B=+1 | −μy | Regression contribution | 4-head/2-task H4 |
| 983 | Negative weighted-score [RG] | ⟦q⟧; weighted-score: A=+2, *B=−2* | ⟦q⟧; weighted-score: *A=−1*, B=+1 | −μy | Regression contribution | 3-head/2-task H1 |
| 984 | Positive weighted-score [RG] | ⟦q⟧; weighted-score: *A=+2*, B=−2 | ⟦q⟧; weighted-score: A=−1, *B=+1* | +μy | Regression contribution | 3-head/2-task H2 |
| 985 | Mixed-sign [RG] | ⟦q⟧; *A:(s₁=−2,s₂=+2)*, B:(+2,−2) | ⟦q⟧; A:(s₁=+1,s₂=−1), *B:(−1,+1)* | −μ₁y₁; +μ₂y₂ | Both tasks | 3-head/2-task H3 |

### Decision Transformer: navigation under requested returns

**T/R/C.** A one-layer, two-head gridworld model. H0 italics are behavioral cues; its routing is unresolved here. H1 attends to its **whole current state token**, not a separate obstacle patch. RTG is requested return. These are context-dependent observations from the authors' experiment. [DT]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 986 | Low-return goal avoidance [DT] | RTG: *−1*. Agent faces south, *goal directly south*. | RTG: *0*. Agent approaches a *goal from the north*. | Anti-forward evidence | Helps avoid goal from above | Toy Decision Transformer H0 |
| 987 | Positive-return obstacle avoidance [DT] | RTG=.9; *⟦state: obstacle ahead⟧* | RTG=.8; *⟦state: facing east, obstacle ahead⟧* | Negative forward-logit contribution | Discourages moving into obstacles | Toy Decision Transformer H1 |

### Vision heads attracted to X-ray annotations

**R.** Italics mark image regions in reported attention patterns; query positions are not specified here. IDs preserve the preprint's numbering convention. Annotation removal affects attention, but ablations do **not** establish a distinctive clinical prediction effect for these heads. [XR]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 988 | Corner annotation [XR] | Chest image with *scanner text in a corner*. | Chest image with a *corner orientation stamp*. | Unknown | Unknown | ViT-Base/16 L8H10 |
| 989 | Corner annotation [XR] | Chest image with *scanner text in a corner*. | Chest image with a *corner orientation stamp*. | Unknown | Unknown | DeiT-Base L9H2 |
| 990 | Corner annotation [XR] | Chest image with *scanner text in a corner*. | Chest image with a *corner orientation stamp*. | Unknown | Unknown | ViT-Large/16 L8H8 |

### Function induction: collaborating heads in off-by-one addition

**R/C.** Gemma=Gemma-2-9B; Llama=Llama-3-8B; zero-based IDs. FI reads demonstration answers; PT reads preceding equals signs. Consolidation reads self/BOS. Payloads remain partly unresolved. Gemma FI/consolidation effects use identity-prompt patching; x is the unchanged answer. PT feeds FI without uniformly helpful signs. Appendices C.2/E. [FX]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 991 | Consolidation [FX] | 0+1=2; 1+2=4; 2+2=5; 3+2=6; 3+3 *⟦=⟧* | 0+0=1; 1+1=3; 1+3=5; 2+3=6; 4+3 *⟦=⟧* | Unknown | Suppresses non-x | Gemma:L41H4 |
| 992 | Consolidation [FX] | 0+1=2; 1+2=4; 2+2=5; 3+2=6; 3+3 *⟦=⟧* | 0+0=1; 1+1=3; 1+3=5; 2+3=6; 4+3 *⟦=⟧* | Unknown | Promotes non-x | Gemma:L41H5 |
| 993 | Consolidation [FX] | 0+1=2; 1+2=4; 2+2=5; 3+2=6; 3+3 *⟦=⟧* | 0+0=1; 1+1=3; 1+3=5; 2+3=6; 4+3 *⟦=⟧* | Unknown | Suppresses non-x | Gemma:L40H11 |
| 994 | Consolidation [FX] | 0+1=2; 1+2=4; 2+2=5; 3+2=6; 3+3 *⟦=⟧* | 0+0=1; 1+1=3; 1+3=5; 2+3=6; 4+3 *⟦=⟧* | Unknown | Suppresses non-x | Gemma:L40H12 |
| 995 | FI [FX] | 0+1=*2*; 1+2=*4*; 2+2=*5*; 3+2=*6*; 3+3 ⟦=⟧ | 0+0=*1*; 1+1=*3*; 1+3=*5*; 2+3=*6*; 4+3 ⟦=⟧ | Partial-function | Promotes x+1 | Gemma:L39H7 |
| 996 | FI [FX] | 0+1=*2*; 1+2=*4*; 2+2=*5*; 3+2=*6*; 3+3 ⟦=⟧ | 0+0=*1*; 1+1=*3*; 1+3=*5*; 2+3=*6*; 4+3 ⟦=⟧ | Partial-function | Partial contribution | Gemma:L39H12 |
| 997 | FI [FX] | 0+1=*2*; 1+2=*4*; 2+2=*5*; 3+2=*6*; 3+3 ⟦=⟧ | 0+0=*1*; 1+1=*3*; 1+3=*5*; 2+3=*6*; 4+3 ⟦=⟧ | Partial-function | Partial contribution | Gemma:L36H7 |
| 998 | FI [FX] | 0+1=*2*; 1+2=*4*; 2+2=*5*; 3+2=*6*; 3+3 ⟦=⟧ | 0+0=*1*; 1+1=*3*; 1+3=*5*; 2+3=*6*; 4+3 ⟦=⟧ | Partial-function | Promotes >x | Gemma:L32H1 |
| 999 | FI [FX] | 0+1=*2*; 1+2=*4*; 2+2=*5*; 3+2=*6*; 3+3 ⟦=⟧ | 0+0=*1*; 1+1=*3*; 1+3=*5*; 2+3=*6*; 4+3 ⟦=⟧ | Partial-function | Partial contribution | Gemma:L32H6 |
| 1000 | FI [FX] | 0+1=*2*; 1+2=*4*; 2+2=*5*; 3+2=*6*; 3+3 ⟦=⟧ | 0+0=*1*; 1+1=*3*; 1+3=*5*; 2+3=*6*; 4+3 ⟦=⟧ | Partial-function | Partial contribution | Gemma:L25H13 |
| 1001 | PT [FX] | 0+1 *=* ⟦2⟧ | 2+3 *=* ⟦6⟧ | Unknown | Feeds FI | Gemma:L38H6 |
| 1002 | PT [FX] | 0+1 *=* ⟦2⟧ | 2+3 *=* ⟦6⟧ | Unknown | Feeds FI | Gemma:L38H7 |
| 1003 | PT [FX] | 0+1 *=* ⟦2⟧ | 2+3 *=* ⟦6⟧ | Unknown | Feeds FI | Gemma:L38H9 |
| 1004 | PT [FX] | 0+1 *=* ⟦2⟧ | 2+3 *=* ⟦6⟧ | Unknown | Feeds FI | Gemma:L35H14 |
| 1005 | PT [FX] | 0+1 *=* ⟦2⟧ | 2+3 *=* ⟦6⟧ | Unknown | Feeds FI | Gemma:L35H9 |
| 1006 | PT [FX] | 0+1 *=* ⟦2⟧ | 2+3 *=* ⟦6⟧ | Unknown | Feeds FI | Gemma:L31H4 |
| 1007 | PT [FX] | 0+1 *=* ⟦2⟧ | 2+3 *=* ⟦6⟧ | Unknown | Feeds FI | Gemma:L31H5 |
| 1008 | PT [FX] | 0+1 *=* ⟦2⟧ | 2+3 *=* ⟦6⟧ | Unknown | Feeds FI | Gemma:L29H5 |
| 1009 | FI [FX] | 11+12=*24*; 13+14=*28*; 15+16=*32*; 17+18=*36*; 19+20 ⟦=⟧ | 20+21=*42*; 22+23=*46*; 24+25=*50*; 26+27=*54*; 28+29 ⟦=⟧ | Unresolved | Contributes | Llama:L26H2 |
| 1010 | FI [FX] | 11+12=*24*; 13+14=*28*; 15+16=*32*; 17+18=*36*; 19+20 ⟦=⟧ | 20+21=*42*; 22+23=*46*; 24+25=*50*; 26+27=*54*; 28+29 ⟦=⟧ | Unresolved | Contributes | Llama:L23H13 |
| 1011 | FI [FX] | 11+12=*24*; 13+14=*28*; 15+16=*32*; 17+18=*36*; 19+20 ⟦=⟧ | 20+21=*42*; 22+23=*46*; 24+25=*50*; 26+27=*54*; 28+29 ⟦=⟧ | Unresolved | Contributes | Llama:L23H15 |
| 1012 | PT [FX] | 11+12 *=* ⟦24⟧ | 22+23 *=* ⟦46⟧ | Unknown | Feeds FI | Llama:L24H10 |
| 1013 | PT [FX] | 11+12 *=* ⟦24⟧ | 22+23 *=* ⟦46⟧ | Unknown | Feeds FI | Llama:L24H11 |
| 1014 | PT [FX] | 11+12 *=* ⟦24⟧ | 22+23 *=* ⟦46⟧ | Unknown | Feeds FI | Llama:L22H25 |
| 1015 | PT [FX] | 11+12 *=* ⟦24⟧ | 22+23 *=* ⟦46⟧ | Unknown | Feeds FI | Llama:L22H27 |
| 1016 | PT [FX] | 11+12 *=* ⟦24⟧ | 22+23 *=* ⟦46⟧ | Unknown | Feeds FI | Llama:L21H7 |

### Bracket completion: stack writers and readout heads

**R/C.** Pythia-1B, final checkpoint 143000; zero-based IDs. Writer payloads are supported by a **group-level** stack-slot/type fit and intervention, not isolated push/pop programs. Writer and L7H2 italics mark task cues. Only L14H1 illustrates directly tested matching-opener routing, which is probabilistic, not perfect. [DY]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 1017 | Stack writer [DY] | Prefix: *( [ ]* | Prefix: *[ ( )* | Slot/type information (group fit) | Supports stack representation (group) | Pythia L1H1 |
| 1018 | Stack writer [DY] | Prefix: *( [ ]* | Prefix: *[ ( )* | Slot/type information (group fit) | Supports stack representation (group) | Pythia L2H1 |
| 1019 | Stack writer [DY] | Prefix: *( [ ]* | Prefix: *[ ( )* | Slot/type information (group fit) | Supports stack representation (group) | Pythia L2H5 |
| 1020 | Bracket readout [DY] | Prefix: *( [ ]* → ) | Prefix: *[ ( )* → ] | Closer evidence | Positive final-checkpoint contribution | Pythia L7H2 |
| 1021 | Matching-opener reader [DY] | *(* [ ⟦]⟧ → ) | *[* ( ⟦)⟧ → ] | Answer-direction contribution | Supports closing-bracket prediction | Pythia L14H1 |

### TabPFN: feature-selective heads in numerical prediction

**C/F.** Feature-wise attention, zero-based IDs. Italics mark **task inputs**, not resolved attention targets. Multiplication means y=ab+c; Pairwise-50 means y=(Σxᵢ)² over 50 features. Patching/ablation localizes contributions without decoding an arithmetic algorithm or OV payload. Negative recovery means interference under the tested corruption. [TP]

| Number | Describes the head briefly | Example 1 | Example 2 | Transmitted feature, if known | Downstream effect, if known | Model / reported layer or head |
| --- | --- | --- | --- | --- | --- | --- |
| 1022 | Multiplication-sensitive [TP] | Predict y from *a=.2, b=.3, c=.1*. | Predict y from *a=.5, b=.4, c=.2*. | Unknown | Largest multiplication ablation effect: .076σ | TabPFN L0H2 |
| 1023 | Selective multiplication contribution [TP] | Predict y from *a=.3, b=.2, c=.4*. | Predict y from *a=.6, b=.5, c=.1*. | Unknown | Peak H2 multiplication restoration | TabPFN L6H2 |
| 1024 | Pairwise-50 interference [TP] | Predict y from *50 features beginning .1, .2, …*. | Predict y from *50 features beginning −.2, .4, …*. | Unknown | Patching recovery −18.5% | TabPFN L13H2 |

## How to turn this into an experimental inventory

My proposed record for an authored head is:

`query condition → source selector → transmitted feature → downstream consumer`

Keep a separate evidence field: `attention observation`, `output association`, `causal circuit evidence`, or `authored hypothesis`. Otherwise a plausible description can quietly become an assumed mechanism.

For example, an **authored** story head could be:

`current entity is a door → retrieve its latest state-changing event → {state: locked, event_id: …} → reduce unsupported “opened” continuations`

That is a design proposal, not an extracted transformer head. Its value could be tested against a grammar-only baseline. A more faithful next-word experiment would let the consumer learn a distributional adjustment rather than hardcoding a single continuation.

Your `flows … river` and `door … opens` observations are useful candidates for another entry, but need the query/source direction and controlled examples recorded first. The pairs alone do not establish “subject finder,” “verb finder,” or a copy operation. Keep them as hypotheses until interventions distinguish those possibilities.

## Sources

The short links in the tables resolve to these primary papers or project documentation. The catalog deliberately distinguishes observed routing, output-feature associations, and demonstrated causal effects.

[F]: https://transformer-circuits.pub/2021/framework/index.html
[H]: https://docs.neuronpedia.org/attention-heads
[I]: https://arxiv.org/html/2211.00593v1
[M]: https://arxiv.org/html/2406.17759v1
[C]: https://aclanthology.org/2024.blackboxnlp-1.22/
[R]: https://arxiv.org/abs/2404.15574
[S]: https://hanlab.mit.edu/projects/streamingllm
[O]: https://arxiv.org/html/2312.09230v1
[B]: https://aclanthology.org/W19-4828/

- [F — A Mathematical Framework for Transformer Circuits][F]
- [H — HeadVis documentation][H]
- [I — Interpretability in the Wild: a Circuit for Indirect Object Identification in GPT-2 Small][I]
- [M — Interpreting Attention Layer Outputs with Sparse Autoencoders, especially §4.2 and Appendix M][M]
- [C — Copy Suppression: Comprehensively Understanding a Motif in Language Model Attention Heads][C]
- [R — Retrieval Head Mechanistically Explains Long-Context Factuality][R]
- [S — Efficient Streaming Language Models with Attention Sinks][S]
- [O — Successor Heads: Recurring, Interpretable Attention Heads In The Wild][O]
- [B — What Does BERT Look at? An Analysis of BERT's Attention][B]

### Additional primary sources for entries 37–136

[HV]: https://transformer-circuits.pub/2026/headvis/index.html
[MT]: https://transformer-circuits.pub/2025/attention-update/index.html
[VO]: https://aclanthology.org/P19-1580/
[SP]: https://aclanthology.org/D19-1223/
[SI]: https://aclanthology.org/2024.findings-acl.412/
[FA]: https://arxiv.org/html/2402.07321v1
[AR]: https://arxiv.org/html/2403.19521v1
[SE]: https://arxiv.org/html/2310.15154v1
[MC]: https://arxiv.org/html/2307.09458v3
[AC]: https://proceedings.mlr.press/v238/garcia-carrasco24a.html
[FV]: https://arxiv.org/html/2310.15213v1
[TR]: https://arxiv.org/html/2502.11806v1
[TM]: https://arxiv.org/html/2502.14258v2
[AD]: https://arxiv.org/html/2502.00873v1
[GT]: https://arxiv.org/html/2305.00586v5
[ST]: https://arxiv.org/html/2402.11004v1
[DR]: https://lacoco-lab.github.io/home/decompiling_transformers/
[IT]: https://arxiv.org/html/2406.02128v1
[SY]: https://arxiv.org/html/2408.08590v1
[CO]: https://adaptive-intelligence.co.uk/wp-content/uploads/2025/12/north2025beyond.pdf
[CT]: https://arxiv.org/html/2502.06923v1
[LW]: https://transformer-circuits.pub/2025/linebreaks/index.html
[TV]: https://openreview.net/pdf/1e59ed4493a1d02a3f0ec9e7633b7f61f0c60fa3.pdf
[ET]: https://arxiv.org/html/2402.14811v1
[RB]: https://arxiv.org/html/2606.08644v1
[CG]: https://doi.org/10.1145/3664606

- [HV — HeadVis: An Interactive Tool for Investigating Attention Heads; fuzzy induction, polysemantic head, answer selection, same-set suppression][HV]
- [MT — Progress on Attention; Multitoken Transcoders (preliminary findings)][MT]
- [VO — Analyzing Multi-Head Self-Attention: Specialized Heads Do the Heavy Lifting, the Rest Can Be Pruned; §5 and Table 1][VO]
- [SP — Adaptively Sparse Transformers; BPE-merging analysis and Figure 8][SP]
- [SI — Identifying Semantic Induction Heads to Understand In-Context Learning; relation probes and reverse-relation results][SI]
- [FA — Summing Up the Facts: Additive Mechanisms Behind Factual Recall in LLMs; §3][FA]
- [AR — Interpreting Key Mechanisms of Factual Recall in Transformer-Based Language Models; argument passing and §4.3][AR]
- [SE — Linear Representations of Sentiment in Large Language Models; Appendix A.3][SE]
- [MC — Does Circuit Analysis Interpretability Scale? Evidence from Multiple Choice Capabilities in Chinchilla; §3.3 and Appendix B][MC]
- [AC — How Does GPT-2 Predict Acronyms? Extracting and Understanding a Circuit via Mechanistic Interpretability; §3–4][AC]
- [FV — Function Vectors in Large Language Models; intervention results and Appendix D][FV]
- [TR — Exploring Translation Mechanism of Large Language Models; §6.1][TR]
- [TM — Does Time Have Its Place? Temporal Heads: Where Language Models Recall Time-specific Information][TM]
- [AD — Language Models Use Trigonometry to Do Addition; §5.2 and Appendix D.1][AD]
- [GT — How Does GPT-2 Compute Greater-Than?; §3.3 and related-task experiments][GT]
- [ST — The Evolution of Statistical Induction Heads: In-Context Learning Markov Chains; training phases and n-gram extension][ST]
- [DR — Decompiling Transformers; extracted most-frequent, sorting, and bounded-Dyck programs][DR]
- [IT — Iteration Head: A Mechanistic Study of Chain-of-Thought; §3.1][IT]
- [SY — A Mechanistic Interpretation of Syllogistic Reasoning in Auto-Regressive Language Models; term flow and suppression][SY]
- [CO — Beyond Syntax: How Do LLMs Understand Code?; Figure 1 and cross-language type analysis][CO]
- [CT — Do Attention Heads Compete or Cooperate During Counting?; Count01 and head aggregation][CT]
- [LW — When Models Manipulate Manifolds: The Geometry of a Counting Task; counting, boundary detection, and visual illusions][LW]
- [TV — From Indirect Object Identification to Syllogisms: Exploring Binary Mechanisms in Transformer Circuits; workshop version, truth heads and modulation][TV]
- [ET — Fine-Tuning Enhances Existing Mechanisms: A Case Study on Entity Tracking; §4–5 and Appendix D][ET]
- [RB — A Retrieval Conditioned Rebinding Circuit for Dynamic Entity Tracking in Large Language Models; §4–5 (preprint)][RB]
- [CG — Unveiling Code Pre-Trained Models: Investigating Syntax and Semantics Capacities; §5.3 attention associations with DDG/CDG/CFG][CG]

### Further primary sources for the 1,024-entry expansion

[NG]: https://arxiv.org/html/2605.03052v1
[TS]: https://arxiv.org/html/2410.09223v1
[AG]: https://aclanthology.org/2021.acl-long.144.pdf
[PL]: https://arxiv.org/html/2609.03687v1
[NA]: https://arxiv.org/html/2610.09571v1
[WM]: https://arxiv.org/html/2412.11867v2
[RT]: https://arxiv.org/html/2602.22453v1
[VS]: https://arxiv.org/html/2603.20662v1

- [NG — How Language Models Process Negation; §4–5, Figure 4][NG]
- [TS — The Same but Different: Structural Similarities and Differences in Multilingual Language Modeling; §4.5][TS]
- [AG — Causal Analysis of Syntactic Agreement Mechanisms in Neural Language Models; Appendix A][AG]
- [PL — A Circuit for Plural Reference; §5 and Appendices C–E][PL]
- [NA — How Do LLMs Change Predictions Under Negation?; §4, Appendices E.4–E.5][NA]
- [WM — Transformers Use Causal World Models in Maze-Solving Tasks; §3.1–3.3][WM]
- [RT — Bridging Latent Reasoning and Target-Language Generation via Retrieval-Transition Heads; §3–5][RT]
- [VS — Attention in Space: Functional Roles of VLM Heads for Spatial Reasoning; §4–6][VS]

[AT]: https://arxiv.org/html/2505.15807v1
[JC]: https://arxiv.org/html/2503.10996v1
[OT]: https://arxiv.org/html/2402.12201v1
[DS]: https://www.alignmentforum.org/posts/u6KXXmKFbXfWzoAXn/a-circuit-for-python-docstrings-in-a-4-layer-attention-only
[PS]: https://www.alignmentforum.org/posts/nuJFTS5iiJKT5G5yh/polysemantic-attention-head-in-a-4-layer-transformer
[WS]: https://arxiv.org/html/2511.13653v1
[BR]: https://arxiv.org/html/2610.09733v1
[SG]: https://arxiv.org/html/2608.18545v1
[RF]: https://arxiv.org/html/2609.00051v1
[CA]: https://arxiv.org/html/2610.09124v1
[VM]: https://arxiv.org/html/2410.24050v1
[DU]: https://arxiv.org/html/2410.10819v1
[OD]: https://arxiv.org/html/2603.26127v1
[VC]: https://arxiv.org/html/2305.00729v1
[FG]: https://arxiv.org/html/2310.01801v2

- [AT — The Atlas of In-Context Learning; §6 and Appendix C][AT]
- [JC — Taming Knowledge Conflicts in Language Models; Table 1][JC]
- [OT — Dictionary Learning Improves Patch-Free Circuit Discovery; Othello-GPT §3.3][OT]
- [DS — A Circuit for Python Docstrings in a 4-Layer Attention-Only Transformer; original investigator report][DS]
- [PS — Polysemantic Attention Head in a 4-Layer Transformer; investigator follow-up][PS]
- [WS — Weight-sparse Transformers Have Interpretable Circuits; §3.2 and Appendix F.2][WS]
- [BR — Bridge Routing Heads; §4 and limitations (preprint)][BR]
- [SG — Shared Circuits for Shared Grammar; person/number contrasts (preprint)][SG]
- [RF — From Detection to Refusal; §3–4 (preprint)][RF]
- [CA — Spatial Induction Heads; §4 and Appendix H (preprint)][CA]
- [VM — A Visual Case Study of the Training Dynamics in Neural Networks; §3][VM]
- [DU — DuoAttention; Figure 1 and §2.1][DU]
- [OD — Finding Distributed Object-Centric Properties in Self-Supervised Transformers; §3–5][OD]
- [VC — What Do Self-Supervised Vision Transformers Learn?; §2 and Appendix E][VC]
- [FG — Model Tells You What to Discard: Adaptive KV Cache Compression for LLMs; §4][FG]

### Primary sources for entries 237–336

[SC]: https://onlinelibrary.wiley.com/doi/full/10.1111/cogs.70187
[PC]: https://arxiv.org/html/2410.16139v1
[VJ]: https://arxiv.org/html/2506.22105v1
[CU]: https://arxiv.org/html/2502.06106v1
[CH]: https://ial.eecs.ucf.edu/pdf/Sukthankar-AGI2024.pdf
[LS]: https://arxiv.org/html/2501.18666v1
[ML]: https://arxiv.org/html/2607.23054v1
[CP]: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0340088
[AH]: https://technion-cs-nlp.github.io/llm-arithmetic-heuristics/paper.pdf
[AN]: https://aclanthology.org/2024.emnlp-main.193.pdf
[PF]: https://arxiv.org/html/2606.16407v1

- [SC — Evidence Against Syntactic Encapsulation in Large Language Models; Table 1 and semantic-plausibility experiments][SC]
- [PC — A Psycholinguistic Evaluation of Language Models’ Sensitivity to Argument Roles; §7][PC]
- [VJ — Identifying a Circuit for Verb Conjugation in GPT-2; Table 4 and §4.4 limitations (preprint)][VJ]
- [CU — Circuit-tuning: A Mechanistic Approach for Identifying Parameter Redundancy and Fine-tuning Neural Networks; Appendix C.4][CU]
- [CH — Decoding Chess Mastery: A Mechanistic Analysis of a Chess Language Transformer Model; §4, Figure 4 and Table 2][CH]
- [LS — Structure Development in List-Sorting Transformers; §3–4 and Appendix B][LS]
- [ML — Through the Bottleneck: How Multi-head Latent Attention Separates Content from Position in Language Models; Table 3 (preprint)][ML]
- [CP — Circuit Explained: How Does a Transformer Perform Compositional Generalization; circuit-discovery sections and Figures 5–11][CP]
- [AH — Arithmetic Without Algorithms: Language Models Solve Math with a Bag of Heuristics; Appendix B.2, Table 2 and Figure 14][AH]
- [AN — Interpreting Arithmetic Mechanism in Large Language Models through Comparative Neuron Analysis; Tables 1–2 and Appendix C][AN]
- [PF — A Mechanistic Understanding of Pronoun Fidelity in LLMs; §6, Table 7 and Appendix G (preprint)][PF]

### Primary sources for entries 337–436

[LG]: https://arxiv.org/html/2601.04260v1
[LK]: https://aclanthology.org/2024.emnlp-main.930.pdf
[ES]: https://aclanthology.org/2023.acl-long.893.pdf
[MP]: https://arxiv.org/html/2412.11965v2
[NN]: https://aclanthology.org/2023.wmt-1.45.pdf

- [LG — Towards a Mechanistic Understanding of Propositional Logical Reasoning in Large Language Models; Figures 7, 13–14, preprint version 1][LG]
- [LK — Interpreting Context Look-ups in Transformers: Investigating Attention–MLP Interactions; Table 2 and Appendix F][LK]
- [ES — Analyzing Transformers in Embedding Space; Appendix C.1][ES]
- [MP — Inferring Functionality of Attention Heads from their Parameters (MAPS); Tables 6–7, Table 25, Appendix D, version 2][MP]
- [NN — A Closer Look at Transformer Attention for Multilingual Translation; Tables 5, 7, 10–11][NN]

### Primary sources for entries 437–540

[PB]: https://arxiv.org/html/2006.15222v3
[SU]: https://irlab.science.uva.nl/wp-content/papercite-data/pdf/baan-2019-do.pdf
[MU]: https://merl.com/publications/docs/TR2024-032.pdf
[LX]: https://arxiv.org/html/2406.00877v1
[LXC]: https://github.com/HumanCompatibleAI/leela-interp/blob/da19a5905375570995dace848c94c794bef70347/src/leela_interp/tools/piece_movement_heads.py
[LY]: https://arxiv.org/html/2505.21552v1
[GR]: https://arxiv.org/html/2608.05467v1
[NS]: https://aclanthology.org/2020.acl-main.429.pdf
[GB]: https://arxiv.org/html/2603.11793v1
[SA]: https://www.isca-archive.org/interspeech_2024/baumann24b_interspeech.pdf
[PH]: https://www.isca-archive.org/interspeech_2022/shim22_interspeech.pdf
[DH]: https://timaeus.co/research/2024-10-04-differentiation-and-specialization

- [PB — BERTology Meets Biology: Interpreting Attention in Protein Language Models; Figures 1–3, Appendix C.5][PB]
- [SU — Do Transformer Attention Heads Provide Transparency in Abstractive Summarization?; Tables 1–2][SU]
- [MU — Understanding and Controlling Generative Music Transformers by Probing Individual Attention Heads; Figures 1–2, Table 2][MU]
- [LX — Evidence of Learned Look-Ahead in a Chess-Playing Neural Network; §3.2][LX]
- [LXC — Author-maintained movement-head lists; pinned repository revision, zero-based indices][LXC]
- [LY — Understanding the Learned Look-Ahead Behavior of Chess Neural Networks; §3, Appendix D][LY]
- [GR — A Mechanistic Analysis of Gender Sensitivity in Dense Retrieval Models; §4, Table 3 (preprint)][GR]
- [NS — How Does BERT's Attention Change When You Fine-tune?; Table A1][NS]
- [GB — Locating Demographic Bias at the Attention-Head Level in CLIP's Vision Encoder; Tables 4–6 (preprint)][GB]
- [SA — Towards Self-Attention Understanding for Automatic Articulatory Processes Analysis in Cleft Lip and Palate Speech; §4.2–4.4][SA]
- [PH — Similarity and Content-based Phonetic Self Attention for Speech Recognition; §2.2, Figure 1][PH]
- [DH — Differentiation and Specialization of Attention Heads via the Refined Local Learning Coefficient; Table 1, Appendix B][DH]

### Primary sources for entries 541–640

[BM]: https://aclanthology.org/2025.emnlp-main.1297.pdf
[LC]: https://arxiv.org/html/2610.25026v1
[EQ]: https://arxiv.org/html/2502.08059v1
[TD]: https://arxiv.org/html/2310.05916v2
[QR]: https://aclanthology.org/2025.emnlp-main.1214.pdf
[QRC]: https://github.com/princeton-pli/QRHead/tree/7a668e79a4cc25dddf1de4058af5c58a141e0c65/src/qrretriever/configs
[RH]: https://arxiv.org/html/2605.07984v1
[RP]: https://arxiv.org/html/2601.20164v1
[PM]: https://arxiv.org/html/2508.02527v2
[WA]: https://arxiv.org/html/2509.09987v1

### Sources for entries 641–740

- [AV — Increasing Trust in Language Models through the Reuse of Verified Circuits; version 6, Appendices I–J and Table 13][AV]
- [GD — Towards Automated Circuit Discovery for Mechanistic Interpretability; Appendices I and K, Figures 21–22][GD]
- [TC — Tracr author repository; README reverse program and compiler/lib.py make_frac_prevs][TC]
- [HR — Cross-Attention Head Position Patterns Can Align with Human Visual Concepts in Text-to-Image Generative Models; §3–4 and Appendix H][HR]
- [HC — HRV author data and extraction notebook, pinned commit b2e4e90; final_result top-1 SD1.4 and top-11 SDXL CSVs][HC]
- [GE — Explainability in transformer models for functional genomics; Figure 3 and promoter-head analysis][GE]
- [VA — Compact Attention: Exploiting Structured Spatio-Temporal Sparsity for Fast Video Generation; §3.2/Figure 3][VA]
- [HM — Controlling Motion Transfer in Diffusion Transformers via Attention Heads; §3/Figure 4 and Appendix D][HM]
- [VI — Interpreting Attention Heads for Image-to-Text Information Flow in Large Vision–Language Models; Appendix C.2/Figure 8][VI]
- [JL — Verbalizable Representations Form a Global Workspace in Language Models; attention-head analysis, Figure 93][JL]

[AV]: https://arxiv.org/html/2402.02619v6
[GD]: https://papers.nips.cc/paper_files/paper/2023/file/34e1dbe95d34d7ebaf99b9bcaeb5b2be-Paper-Conference.pdf
[TC]: https://github.com/google-deepmind/tracr
[HR]: https://arxiv.org/html/2412.02237v2
[HC]: https://github.com/SNU-DRL/HRV/tree/b2e4e90b9f4f9f84d8af0198f587e192a3292c8c
[GE]: https://academic.oup.com/bib/article/22/5/bbab060/6214646
[VA]: https://arxiv.org/html/2508.12969v1
[HM]: https://arxiv.org/html/2607.11081v1
[VI]: https://arxiv.org/html/2509.17588v1
[JL]: https://transformer-circuits.pub/2026/workspace/index.html

### Sources for entries 741–840

Appendix M reuses [M]. Six additional sources:

- [SX — Spectral Probe-Circuits: A Three-Step Recipe for Identifying Attention-Head Circuits in Pretrained Transformers; §§4–5, preprint][SX]
- [UT — How Do Agentic LLMs Decide to Call Tools? A Tool-Call Vector Shaped by Suppression; Appendix E, preprint][UT]
- [LR — A Implies B: Circuit Analysis in LLMs for Propositional Logical Reasoning; Appendices B.4–B.11, NeurIPS 2025][LR]
- [KC — Knowledge Circuits in Pretrained Transformers; §4 and Figures 1–3, NeurIPS 2024][KC]
- [VB — Analyzing the Structure of Attention in a Transformer Language Model; §5.3 and Tables 1–3][VB]
- [CS — How Do LLMs Generate Contrastive Sentiments? A Mechanistic Perspective; §6 and Appendix C.4, EACL 2026][CS]

[SX]: https://arxiv.org/html/2605.24059v1
[UT]: https://arxiv.org/html/2610.09624v1
[LR]: https://papers.neurips.cc/paper_files/paper/2025/file/2c4477572f06102b2ae3bd2b2ffcebf9-Paper-Conference.pdf
[KC]: https://papers.nips.cc/paper_files/paper/2024/file/d6df31b1be98e04be48af8bedb95b499-Paper-Conference.pdf
[VB]: https://arxiv.org/html/1906.04284v1
[CS]: https://aclanthology.org/2026.eacl-long.311.pdf




- [BM — Pathway to Relevance: How Cross-Encoders Implement a Semantic Variant of BM25; §4.1–4.3, final EMNLP paper][BM]
- [LC — One Head Away from Language Confusion: Single Attention Heads Across Model Families; Table 1, §6.1, Appendix H (preprint)][LC]
- [EQ — On Mechanistic Circuits for Extractive Question-Answering; Figures 7–10 and 16][EQ]
- [TD — Interpreting CLIP's Image Representation via Text-Based Decomposition; Appendix A.4][TD]
- [QR — Query-Focused Retrieval Heads Improve Long-Context Reasoning and Re-ranking; §3][QR]
- [QRC — QRHead author configurations; first four entries of each cited model's qr_head_NQ.yaml, pinned revision][QRC]
- [RH — Where's the Plan? Locating Latent Planning in Language Models with Lightweight Mechanistic Interventions; §4.1 (preprint)][RH]
- [RP — What's the Plan? Metrics for Implicit Planning in LLMs and Their Application to Rhyme Generation and Question Answering; §4.6][RP]
- [PM — I Have No Mouth, and I Must Rhyme: Uncovering Internal Phonetic Representations in LLaMA 3.2; §3][PM]
- [WA — Whisper Has an Internal Word Aligner; Figure 5 and §IV-C][WA]

### Sources added for entries 841–940

- [TO — Temporal Token Matters: Investigating and Interpreting the Consistency of Temporal Ordering in Large Language Models; Appendices B–C][TO]
- [FI — LLMs Process Lists With General Filter Heads; §2, Appendices I and N][FI]
- [AB — Emergent Symbolic Mechanisms Support Abstract Reasoning in Large Language Models; §§2–3, Appendix C.5][AB]
- [MA — Molecule Attention Transformer; Appendix G, Table 19][MA]
- [MG — Circuits, Features, and Heuristics in Molecular Transformers; §3.1, Table 1][MG]
- [SM — SMolLM: Small Language Models Learn Small Molecular Grammar; §4.3, Table 3][SM]
- [CN — Mechanistic Interpretability of Large-Scale Counting in LLMs through a System-2 Strategy; §§4–5][CN]
- [CL — How and where does CLIP process negation?; Figures 4, 6–7][CL]
- [BL — Language Models Use Lookbacks to Track Beliefs; §§4–6][BL]
- [TI — Mechanistic Interpretability for Transformer-based Time Series Classification; §5][TI]
- [QK — Listening to the Wise Few: Query–Key Alignment Unlocks Latent Correct Answers in Large Language Models; Figure 6, Tables 7–8][QK]
- [DI — The Dual-Route Model of Induction; Figure 3b, §§2–4][DI]
- [AA — Assign and Add: A Mechanistic Study of Compositional Arithmetic; §5][AA]
- [DC — Revealing Algorithmic Deductive Circuits for Logical Reasoning; Figure 3, §4.2][DC]

[TO]: https://aclanthology.org/2026.findings-acl.123.pdf
[FI]: https://arxiv.org/html/2510.26784v1
[AB]: https://arxiv.org/html/2502.20332v2
[MA]: https://arxiv.org/pdf/2002.08264
[MG]: https://arxiv.org/html/2512.09757v1
[SM]: https://arxiv.org/html/2605.06322v1
[CN]: https://arxiv.org/html/2601.02989v1
[CL]: https://aclanthology.org/2024.alvr-1.5.pdf
[BL]: https://arxiv.org/html/2505.14685v2
[TI]: https://arxiv.org/html/2511.21514v1
[QK]: https://arxiv.org/html/2410.02343v2
[DI]: https://arxiv.org/html/2504.03022v2
[AA]: https://arxiv.org/html/2605.31497v1
[DC]: https://arxiv.org/html/2605.27824v1

### Sources added for entries 941–1024

- [SQ — TinySQL: A Progressive Text-to-SQL Dataset for Mechanistic Interpretability Research; Appendix H, Table 11][SQ]
- [HP — Head Pursuit: Probing Attention Specialization in Multimodal Transformers; Table 1, §§4.2 and 5.2][HP]
- [RG — In-Context Linear Regression Demystified: Training Dynamics and Mechanistic Interpretability of Multi-Head Softmax Attention; §3 and Appendix A.3][RG]
- [DT — Decision Transformer Interpretability; authors' primary research write-up, goal/obstacle ablations and QK/OV analysis][DT]
- [XR — Spurious Attention Heads in Vision Transformers: Mechanistic Identification of Annotation-Driven Bias in Medical Chest X-Ray Analysis; §4, preprint][XR]
- [FX — Function Induction and Task Generalization: An Interpretability Study with Off-by-One Addition; Appendices C.2 and E][FX]
- [DY — Bridging Singular Learning Theory and Mechanistic Interpretability at the Billion-Parameter Scale; §5.1 and Appendix Q, preprint][DY]
- [TP — Where Computation Lives Inside TabPFN: Causal Localisation of Attention Head Function; §2.4, preprint][TP]

[SQ]: https://arxiv.org/html/2503.12730v2
[HP]: https://arxiv.org/html/2510.21518v1
[RG]: https://arxiv.org/html/2503.12734v1
[DT]: https://www.alignmentforum.org/posts/bBuBDJBYHt39Q5zZy/decision-transformer-interpretability
[XR]: https://arxiv.org/html/2610.21638v1
[FX]: https://arxiv.org/html/2507.09875v3
[DY]: https://arxiv.org/html/2611.00640v1
[TP]: https://arxiv.org/html/2606.12917v1


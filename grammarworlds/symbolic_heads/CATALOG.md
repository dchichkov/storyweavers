# Symbolic head library: descriptions and examples

Generated from the editable [JSON specifications](data/). All weights and examples are authored illustrations, not trained statistics.

**64 heads: 15 executable lookup heads and 49 explicit program-required contracts. Each has ten examples (640 total).** Deferred examples describe desired behavior; they are not claims that the algorithm runs. See [runtime and table semantics](README.md).

## P001 — Subject-number retrieval

Current clause → grammatical subject → number. Reweight singular/plural verb forms.

**Status:** `table`. [Editable specification](data/P001.json).

Supply current, scoped records in channel grammatical_subject. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P001.01 | Plural boats governs agreement despite singular pier nearby. | `present_be` → `boats` → `plural:1` | are / is |
| P001.02 | One boat remains singular despite nearby rocks. | `present_be` → `boat` → `singular:1` | is / are |
| P001.03 | Children is an irregular plural. | `past_be` → `children` → `plural:1` | were / was |
| P001.04 | One child controls past copula agreement. | `past_be` → `child` → `singular:1` | was / were |
| P001.05 | Mass noun bread takes singular agreement. | `present_be` → `bread` → `singular:1` | is / are |
| P001.06 | Scissors has plural grammatical form. | `present_be` → `scissors` → `plural:1` | are / is |
| P001.07 | This seed uses singular collective agreement for flock. | `present_be` → `flock` → `singular:1` | is / are |
| P001.08 | Mice transmits plural rather than a suffix heuristic. | `past_be` → `mice` → `plural:1` | were / was |
| P001.09 | News ends in s but is grammatically singular. | `past_be` → `news` → `singular:1` | was / were |
| P001.10 | A coordinated subject transmits plural. | `present_be` → `Mira_and_Theo` → `plural:1` | are / is |

## P002 — Person agreement

Current finite verb slot → subject's discourse person. Prefer am/is/are as appropriate.

**Status:** `table`. [Editable specification](data/P002.json).

Supply current, scoped records in channel subject_person. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P002.01 | Speaker I selects am. | `present_be` → `I` → `first_singular:1` | am / is |
| P002.02 | Addressee you selects are. | `present_be` → `you` → `second:1` | are / am |
| P002.03 | She selects third-person singular. | `present_be` → `she` → `third_singular:1` | is / am |
| P002.04 | He shares third-person singular with she. | `present_be` → `he` → `third_singular:1` | is / am |
| P002.05 | Inanimate it also selects is. | `present_be` → `it` → `third_singular:1` | is / am |
| P002.06 | We changes person and number from I. | `present_be` → `we` → `first_plural:1` | are / am |
| P002.07 | They selects are. | `present_be` → `they` → `third_plural:1` | are / is |
| P002.08 | Past indicative I selects was in this seed. | `past_be` → `I` → `first_singular:1` | was / were |
| P002.09 | Past you selects were. | `past_be` → `you` → `second:1` | were / was |
| P002.10 | Past we selects were. | `past_be` → `we` → `first_plural:1` | were / was |

## P003 — Tense anchoring

Current event → governing temporal frame. Reweight tense-compatible forms.

**Status:** `table`. [Editable specification](data/P003.json).

Supply current, scoped records in channel temporal_anchor. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P003.01 | Yesterday favors past walking. | `walk` → `yesterday` → `past:1` | walked / walks |
| P003.02 | Last night favors past opening. | `open` → `last_night` → `past:1` | opened / opens |
| P003.03 | Habitual present play in a present-tense frame. | `play` → `every_day` → `habitual_present:1` | plays / played |
| P003.04 | Now anchors a present simple wait clause. | `wait` → `now` → `present:1` | waits / waited |
| P003.05 | Tomorrow favors a future auxiliary before leave. | `leave` → `tomorrow` → `future:1` | will / left |
| P003.06 | Next week favors future arrival. | `arrive` → `next_week` → `future:1` | will / arrived |
| P003.07 | Remote past uses irregular sang. | `sing` → `long_ago` → `past:1` | sang / sings |
| P003.08 | Seasonal habitual growth uses present in this frame. | `grow` → `each_spring` → `habitual_present:1` | grows / grew |
| P003.09 | Completed earlier event uses past. | `finish` → `earlier_today` → `past:1` | finished / finishes |
| P003.10 | Later in a future frame favors will return. | `return` → `later` → `future:1` | will / returned |

## P004 — Auxiliary complement

Unfinished verb phrase → nearest governing auxiliary. Prefer compatible participles or infinitives.

**Status:** `table`. [Editable specification](data/P004.json).

Supply current, scoped records in channel governing_auxiliary. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P004.01 | Modal can takes a bare infinitive. | `walk` → `can` → `bare:1` | walk / walked |
| P004.02 | Might takes swim. | `swim` → `might` → `bare:1` | swim / swam |
| P004.03 | Must takes open. | `open` → `must` → `bare:1` | open / opened |
| P004.04 | Will takes go. | `go` → `will` → `bare:1` | go / went |
| P004.05 | Perfect has selects seen. | `see` → `has` → `participle:1` | seen / saw |
| P004.06 | Perfect had selects written. | `write` → `had` → `participle:1` | written / wrote |
| P004.07 | Progressive is selects running. | `run` → `is_progressive` → `gerund:1` | running / ran |
| P004.08 | Progressive was selects singing. | `sing` → `was_progressive` → `gerund:1` | singing / sang |
| P004.09 | Passive was selects broken. | `break` → `was_passive` → `participle:1` | broken / broke |
| P004.10 | The parsed chain has been selects working. | `work` → `has_been_progressive` → `gerund:1` | working / worked |

## P005 — Determiner completion

Unfinished noun phrase → active determiner. Reweight noun forms.

**Status:** `table`. [Editable specification](data/P005.json).

Supply current, scoped records in channel active_determiner. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P005.01 | A takes one countable animal. | `animal` → `a` → `count_singular:1` | cat / cats |
| P005.02 | These takes plural animals. | `animal` → `these` → `count_plural:1` | cats / cat |
| P005.03 | Each selects singular container. | `container` → `each` → `count_singular:1` | cup / cups |
| P005.04 | Several selects plural containers. | `container` → `several` → `count_plural:1` | cups / cup |
| P005.05 | Much selects mass water, not plural bottles. | `liquid` → `much` → `mass:1` | water / bottles |
| P005.06 | Little in this quantity sense selects mass rice. | `food` → `little` → `mass:1` | rice / apples |
| P005.07 | Those selects plural vehicles. | `vehicle` → `those` → `count_plural:1` | boats / boat |
| P005.08 | Every selects one grammatical tool. | `tool` → `every` → `count_singular:1` | hammer / hammers |
| P005.09 | Many selects plural plants. | `plant` → `many` → `count_plural:1` | trees / tree |
| P005.10 | This can select mass cloth. | `fabric` → `this` → `singular_or_mass:1` | cloth / ribbons |

## P006 — Verb argument expectation

Current predicate → its unfilled argument slots. Favor a location or transferred object.

**Status:** `table`. [Editable specification](data/P006.json).

Supply current, scoped records in channel predicate_argument_state. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P006.01 | Put the cup still needs a location. | `put` → `patient_filled` → `location_remaining:1` | on / quickly |
| P006.02 | Give Nia can continue with an object determiner. | `give` → `recipient_filled` → `patient_remaining:1` | a / to |
| P006.03 | Lend the rope can introduce its recipient. | `lend` → `patient_filled` → `recipient_remaining:1` | to / under |
| P006.04 | Sleep permits an adverb rather than a direct object. | `sleep` → `subject_filled` → `no_object:1` | peacefully / the |
| P006.05 | Depend introduces its complement with on. | `depend` → `subject_filled` → `on_complement:1` | on / into |
| P006.06 | Listen introduces a target with to. | `listen` → `subject_filled` → `to_complement:1` | to / of |
| P006.07 | Fill the cup introduces its contents with with. | `fill` → `patient_filled` → `with_complement:1` | with / from |
| P006.08 | Remove the lid may name its source. | `remove` → `patient_filled` → `from_complement:1` | from / at |
| P006.09 | Tell Nia can introduce a content clause. | `tell` → `recipient_filled` → `content_remaining:1` | that / under |
| P006.10 | Become selects a predicative adjective here. | `become` → `subject_filled` → `predicative_remaining:1` | quiet / quietly |

## P007 — Coordination parallelism

After conjunction → first conjunct's structure. Favor a parallel continuation.

**Status:** `table`. [Editable specification](data/P007.json).

Supply current, scoped records in channel first_conjunct_structure. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P007.01 | Singing and dancing maintains gerund form. | `and` → `singing` → `gerund:1` | dancing / danced |
| P007.02 | Quiet but alert coordinates adjectives. | `but` → `quiet` → `adjective:1` | alert / alertly |
| P007.03 | Quickly and carefully coordinates adverbs. | `and` → `quickly` → `adverb:1` | carefully / careful |
| P007.04 | Walked and rested shares tense. | `and` → `walked` → `past_verb:1` | rested / rest |
| P007.05 | To swim or to run repeats infinitive structure. | `or` → `to_swim` → `infinitive:1` | to / swam |
| P007.06 | A cup and a bowl coordinates noun phrases. | `and` → `a_cup` → `noun_phrase:1` | a / walked |
| P007.07 | Tired but hopeful shares category. | `but` → `tired` → `adjective:1` | hopeful / hopefully |
| P007.08 | Under the bed or behind the chair shares phrase type. | `or` → `under_the_bed` → `preposition_phrase:1` | behind / hidden |
| P007.09 | Has eaten and has rested repeats the auxiliary frame. | `and` → `has_eaten` → `perfect_clause:1` | has / ate |
| P007.10 | Softly and slowly shares adverb form. | `and` → `softly` → `adverb:1` | slowly / slow |

## P008 — Clause-boundary tracking

Current prefix → unmatched clause openers. Favor a main clause when still required.

**Status:** `program_required`. [Editable specification](data/P008.json).

**Raises `ProgramRequired`:** Maintain an incremental clause stack from grammatical derivations; distinguish nested subordinate clauses from completed main clauses.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P008.01 | Although rain fell, the prefix ends at the comma. | main_clause_required |
| P008.02 | If the latch breaks, the prefix ends at the comma. | consequent_required |
| P008.03 | Because Mira left, the prefix ends at the comma. | main_clause_required |
| P008.04 | When the bell rang, Theo smiled. | no_open_subordinate_clause |
| P008.05 | Mira said that Nia believed that the gate was open. | nested_complements_completed |
| P008.06 | The sailor who found the map | relative_closed_main_predicate_required |
| P008.07 | The cup that Theo said Nia broke | relative_closed_main_predicate_required |
| P008.08 | Mira wondered whether | embedded_question_open |
| P008.09 | After the boat sank | temporal_clause_requires_main_clause |
| P008.10 | Nia laughed. | sentence_complete |

## P009 — Repeated-prefix continuation

Current suffix → earlier matching suffix and successor. Boost observed continuations proportionally.

**Status:** `program_required`. [Editable specification](data/P009.json).

**Raises `ProgramRequired`:** Index prior token spans and match variable-length current suffixes; count their observed successors without reading future tokens.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P009.01 | Earlier brass bell; current suffix brass. | bell:1 |
| P009.02 | Earlier quiet garden; current suffix quiet. | garden:1 |
| P009.03 | Earlier red boat, red kite; current suffix red. | boat:0.5,kite:0.5 |
| P009.04 | Earlier old red boat and new red kite; suffix old red. | boat:1 |
| P009.05 | Earlier silver key twice and silver cup once; suffix silver. | key:2/3,cup:1/3 |
| P009.06 | Earlier bright moon; suffix dark. | no_match |
| P009.07 | Earlier A B C and A B D; suffix A B. | C:0.5,D:0.5 |
| P009.08 | Earlier wave wave foam; suffix wave wave. | foam:1 |
| P009.09 | Earlier small blue box; suffix small blue. | box:1 |
| P009.10 | Only the current unfinished brass occurs. | no_prior_successor |

## P010 — Entity-name retrieval

Current entity ID → previous surface names. Favor established names over new ones.

**Status:** `program_required`. [Editable specification](data/P010.json).

**Raises `ProgramRequired`:** Join dynamic entity IDs to their established alias records and scoped mention counts; do not bake names into a global lexical table.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P010.01 | Entity e1 has been introduced as Mira twice. | e1:{Mira:2} |
| P010.02 | Entity e2 has aliases Theodore and Theo, used once and three times. | e2:{Theodore:1,Theo:3} |
| P010.03 | Two different entities are both named Sam. Query e3. | aliases_of_e3_only |
| P010.04 | The captain and Nia refer to the same established entity. | aliases:{captain,Nia} |
| P010.05 | An unnamed traveler has no proper-name record. | no_invented_name |
| P010.06 | An entity is renamed Star after being called Puppy. | current_alias:Star;previous_alias:Puppy |
| P010.07 | The building named Rose is distinct from Rose the gardener. | kind_bound_aliases |
| P010.08 | Entity e8 appears only as the miller. | alias:the_miller |
| P010.09 | Omar is mentioned only in another scene's unresolved quotation. | exclude_unbound_quotation_alias |
| P010.10 | A new entity uses the unseen name Zeli. | retrieve_Zeli_without_table_edit |

## P011 — Pronoun antecedent distribution

Current pronoun slot → compatible salient entities. Favor compatible pronouns; retain ambiguity.

**Status:** `program_required`. [Editable specification](data/P011.json).

**Raises `ProgramRequired`:** Resolve dynamic candidate referents using agreement, salience, binding constraints, and ambiguity; return a distribution, not a fixed pronoun dictionary.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P011.01 | Mira arrived; she is the only compatible salient referent. | Mira:1 |
| P011.02 | Theo and Nia arrived as one group. | group:{Theo,Nia} |
| P011.03 | Mira spoke to Nia; both are compatible with she. | ambiguous:{Mira,Nia} |
| P011.04 | The box beside the table is the subject; it follows. | box_preferred_over_table |
| P011.05 | The children saw the teacher; they follows. | children_preferred |
| P011.06 | Mira told Theo about herself. | reflexive_bound_to_Mira |
| P011.07 | Theo told Mira about himself. | reflexive_bound_to_Theo |
| P011.08 | Two boats and one rope are present; it follows. | rope_preferred_by_number |
| P011.09 | Singular they is the established pronoun for Alex. | Alex_supported |
| P011.10 | No entity has been introduced before she. | unresolved_reference |

## P012 — Lexical repetition suppression

Current candidate → recent uses and their predicted mass. Reduce excess repetition, without a blanket ban.

**Status:** `program_required`. [Editable specification](data/P012.json).

**Raises `ProgramRequired`:** Count recent token/lemma usage, compare predicted mass to a baseline, and apply a graded penalty with exemptions for required names or quotations.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P012.01 | Lantern repeats five times and is overpredicted again. | strong_repetition_penalty |
| P012.02 | Lantern occurs once in a necessary first reference. | no_repetition_penalty |
| P012.03 | Quiet appears in three consecutive descriptions. | adjective_penalty |
| P012.04 | The grammar requires the proper name Mira to disambiguate. | preserve_required_reference |
| P012.05 | A quoted refrain repeats ring intentionally. | quotation_exemption |
| P012.06 | Walked and walking repeat the same lemma. | lemma_level_repetition_signal |
| P012.07 | Two uses of key are separated by many paragraphs. | decayed_penalty |
| P012.08 | The word the repeats as a function word. | function_word_exemption |
| P012.09 | A repeated name has low predicted mass already. | small_or_zero_adjustment |
| P012.10 | Boat is frequent in the story but absent from recent context. | distinguish_global_frequency_from_local_repetition |

## P013 — Sense disambiguation

Ambiguous word → nearby sense-bearing relations. Reweight sense-compatible words.

**Status:** `table`. [Editable specification](data/P013.json).

Supply current, scoped records in channel sense_cue. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P013.01 | River selects the water-edge sense of bank. | `bank` → `river` → `water_edge:1` | muddy / financial |
| P013.02 | Deposit selects the financial sense of bank. | `bank` → `deposit` → `finance:1` | financial / muddy |
| P013.03 | Cave suggests the flying animal bat. | `bat` → `cave` → `animal:1` | flew / swung |
| P013.04 | Baseball suggests the sports bat. | `bat` → `baseball` → `sports_tool:1` | swung / flew |
| P013.05 | Wetland suggests the bird crane. | `crane` → `wetland` → `bird:1` | nested / hoisted |
| P013.06 | Construction suggests the lifting crane. | `crane` → `construction` → `machine:1` | hoisted / nested |
| P013.07 | Winter supplies seasonal context for spring. | `spring` → `winter` → `season:1` | bloomed / coiled |
| P013.08 | Mattress supplies a mechanical spring cue. | `spring` → `mattress` → `coil:1` | coiled / bloomed |
| P013.09 | Ocean suggests an animal seal. | `seal` → `ocean` → `animal:1` | swam / stamped |
| P013.10 | Envelope suggests a closure or stamp sense. | `seal` → `envelope` → `closure:1` | stamped / swam |

## P014 — Whole-name completion

Partial established name → remaining name tokens. Favor the remaining name component.

**Status:** `program_required`. [Editable specification](data/P014.json).

**Raises `ProgramRequired`:** Match partial tokenized names against the active entity registry, preserving shared prefixes, capitalization, and dynamic names.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P014.01 | Known name Silver Cove; prefix Silver. | Cove |
| P014.02 | Known name Old Mill; prefix Old. | Mill |
| P014.03 | Known names Red Hill and Red Harbor; prefix Red. | Hill_or_Harbor |
| P014.04 | Known name The Three Pines; prefix The Three. | Pines |
| P014.05 | Known name North by West; prefix North by. | West |
| P014.06 | Known name Blue; prefix Blue. | name_already_complete |
| P014.07 | Unknown prefix Golden has no registry match. | no_match |
| P014.08 | Known name New Stone Bridge; prefix New. | Stone |
| P014.09 | Known name Lake Mira; prefix Lake in another entity scope. | reject_wrong_scope |
| P014.10 | A newly registered name Zeli Tor; prefix Zeli. | Tor_without_static_table_edit |

## P015 — Ordered successor

Current sequence item → configured ordering. Favor a successor in that ordering.

**Status:** `table`. [Editable specification](data/P015.json).

Supply current, scoped records in channel ordered_item. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P015.01 | Monday advances to Tuesday. | `weekday` → `Monday` → `Tuesday:1` | Tuesday / Sunday |
| P015.02 | Friday advances to Saturday. | `weekday` → `Friday` → `Saturday:1` | Saturday / Thursday |
| P015.03 | January advances to February. | `month` → `January` → `February:1` | February / December |
| P015.04 | Months wrap from December to January. | `month` → `December` → `January:1` | January / November |
| P015.05 | Counting advances one to two. | `digit` → `one` → `two:1` | two / zero |
| P015.06 | Counting advances eight to nine. | `digit` → `eight` → `nine:1` | nine / seven |
| P015.07 | Alphabetical A advances to B. | `letter` → `A` → `B:1` | B / Z |
| P015.08 | Alphabetical M advances to N. | `letter` → `M` → `N:1` | N / L |
| P015.09 | The configured season cycle advances summer to autumn. | `season` → `summer` → `autumn:1` | autumn / spring |
| P015.10 | Ordinal second advances to third. | `ordinal` → `second` → `third:1` | third / first |

## P016 — Register continuity

Current passage → recent register-bearing choices. Favor locally compatible diction.

**Status:** `table`. [Editable specification](data/P016.json).

Supply current, scoped records in channel register_cue. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P016.01 | Honored guest suggests a formal greeting. | `greeting` → `honored` → `formal:1` | Greetings / Hey |
| P016.02 | Pal suggests a casual greeting. | `greeting` → `pal` → `casual:1` | Hey / Greetings |
| P016.03 | Kindly favors polite request wording. | `request` → `kindly` → `formal:1` | please / gimme |
| P016.04 | Buddy permits casual wording in this illustrative seed. | `request` → `buddy` → `casual:1` | gimme / kindly |
| P016.05 | Farewell suggests formal departure diction. | `departure` → `farewell` → `formal:1` | departed / split |
| P016.06 | See ya suggests informal departure diction. | `departure` → `see_ya` → `casual:1` | split / departed |
| P016.07 | Thou cues archaic second-person wording. | `description` → `thou` → `archaic:1` | art / are |
| P016.08 | You cues modern wording. | `description` → `you` → `modern:1` | are / art |
| P016.09 | Indeed suggests formal assent. | `agreement` → `indeed` → `formal:1` | Certainly / Yep |
| P016.10 | Yeah suggests casual assent. | `agreement` → `yeah` → `casual:1` | Yep / Certainly |

## P017 — Current location

Entity-focused query → latest valid location event. Favor grounded location words.

**Status:** `program_required`. [Editable specification](data/P017.json).

**Raises `ProgramRequired`:** Resolve an entity ID and replay or query its latest committed location, with movement chronology and entity-specific provenance.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P017.01 | Mira enters the shed after leaving the garden. | Mira:shed |
| P017.02 | Theo walks into the orchard. | Theo:orchard |
| P017.03 | The cup is carried from table to shelf. | cup:shelf |
| P017.04 | Nia exits the cottage into the courtyard. | Nia:courtyard |
| P017.05 | The boat drifts from harbor to cove. | boat:cove |
| P017.06 | Omar remains in the kitchen while Mira leaves. | Omar:kitchen |
| P017.07 | A key moves twice, drawer to pocket to box. | key:box |
| P017.08 | A report says Mira is at the mill but no world move is committed. | preserve_world_location_separate_from_report |
| P017.09 | An entity's only location record was invalidated. | location_unknown |
| P017.10 | Two entities named Sam move to different places. | location_by_entity_id |

## P018 — Current ownership

Object-focused query → latest valid transfer. Favor the current owner.

**Status:** `program_required`. [Editable specification](data/P018.json).

**Raises `ProgramRequired`:** Replay valid ownership transfers by object ID, distinguishing possession, loans, gifts, return, and failed transfers.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P018.01 | Mira gives her cup to Nia. | owner:Nia |
| P018.02 | Theo returns a borrowed map to Omar. | owner:Omar |
| P018.03 | Nia lends her rope to Mira. | owner:Nia;holder:Mira |
| P018.04 | Omar finds a lost ring whose owner is known as Theo. | owner:Theo;holder:Omar |
| P018.05 | Mira offers a key but Nia declines. | owner_unchanged |
| P018.06 | A cup passes Mira to Theo to Nia as gifts. | owner:Nia |
| P018.07 | Two blue cups have distinct object IDs and owners. | preserve_object_identity |
| P018.08 | The group jointly owns the boat. | joint_owners |
| P018.09 | A thief takes a cup without a transfer of title. | distinguish_holder_from_owner |
| P018.10 | No ownership was established for the stone. | owner_unknown |

## P019 — Object condition

Proposed action → latest state of its patient. Downweight unsupported state-dependent actions.

**Status:** `program_required`. [Editable specification](data/P019.json).

**Raises `ProgramRequired`:** Read current object properties from committed state and evaluate action-specific compatibility; stale or hypothetical states must not become facts.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P019.01 | The door is locked; opening is proposed without unlocking. | locked;opening_unsupported |
| P019.02 | The cup is cracked; carrying hot liquid is proposed. | cracked;leak_risk |
| P019.03 | The lamp is unlit; reading in its light is proposed. | unlit;illumination_missing |
| P019.04 | The rope is cut; climbing on it is proposed. | cut;support_missing |
| P019.05 | The boat is repaired after an earlier leak. | repaired;stale_leak_overridden |
| P019.06 | The paint is wet; stacking boards is proposed. | wet;contact_risk |
| P019.07 | The battery is empty; lighting a torch is proposed. | depleted;power_missing |
| P019.08 | The window is open; closing it is proposed. | open;closing_compatible |
| P019.09 | Mira imagines a broken cup, but the real cup is intact. | intact;exclude_imagination |
| P019.10 | An object has no relevant state record. | state_unknown |

## P020 — Containment chain

Object query → nested container relations. Favor reachable containment descriptions.

**Status:** `program_required`. [Editable specification](data/P020.json).

**Raises `ProgramRequired`:** Traverse typed containment relations with cycle detection, current-state resolution, and holder/location distinctions.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P020.01 | Key in box in shed. | key:[box,shed] |
| P020.02 | Ring in pouch in chest in attic. | ring:[pouch,chest,attic] |
| P020.03 | Letter in Mira's pocket while Mira is in garden. | letter:[pocket,Mira,garden] |
| P020.04 | Cup on table in kitchen. | relation_path:[on_table,in_kitchen] |
| P020.05 | Coin moves from bag to drawer. | coin:[drawer] |
| P020.06 | Box and key erroneously contain each other. | cycle_error |
| P020.07 | Two boxes contain different keys. | path_by_object_id |
| P020.08 | A sealed bottle contains water and sits in a crate. | water:[bottle,crate] |
| P020.09 | A cloud is above the house, not inside it. | reject_spatial_as_containment |
| P020.10 | No container is known for the stone. | empty_or_unknown_path |

## P021 — Reachability

Proposed interaction → actor/object positions and barriers. Reweight immediate manipulation versus approach.

**Status:** `program_required`. [Editable specification](data/P021.json).

**Raises `ProgramRequired`:** Search the spatial/access graph using actor capabilities, barriers, container state, and path costs.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P021.01 | Mira is outside a locked shed; key inside. | blocked_by_locked_shed |
| P021.02 | Theo holds a cup. | immediately_reachable |
| P021.03 | Map on high shelf; ladder available nearby. | reachable_after_ladder_use |
| P021.04 | Ring inside sealed chest; no key. | inaccessible |
| P021.05 | Boat across a river; bridge intact. | reachable_via_bridge |
| P021.06 | Boat across a river; bridge destroyed. | route_blocked |
| P021.07 | Nia can fly to a ledge; Omar cannot. | actor_specific_reachability |
| P021.08 | Doorway is too narrow for a large crate. | object_path_constraint |
| P021.09 | Actor and target positions are unknown. | reachability_unknown |
| P021.10 | Two routes exist; one is blocked and one is open. | select_open_route |

## P022 — Resource sufficiency

Proposed action → required and available quantities. Favor acquisition or feasible action.

**Status:** `program_required`. [Editable specification](data/P022.json).

**Raises `ProgramRequired`:** Perform unit-aware resource accounting over inventories and action requirements, reserving shared resources without mutating state during prediction.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P022.01 | Two boards available; repair requires three. | deficit:1_board |
| P022.02 | One candle available; task requires one. | sufficient |
| P022.03 | Half a liter available; task needs 750 milliliters. | deficit:250_milliliters |
| P022.04 | Three coins reserved elsewhere; only one free coin remains. | available:1_coin |
| P022.05 | Two actors both plan to consume the same loaf. | shared_resource_conflict |
| P022.06 | One plank is broken and unusable. | exclude_unusable_inventory |
| P022.07 | Task requires flour but only sand exists. | resource_type_mismatch |
| P022.08 | Reusable hammer needed for two sequential jobs. | no_consumption_deficit |
| P022.09 | Unknown amount of paint remains. | sufficiency_unknown |
| P022.10 | Four meters of rope needed; two pieces of two meters cannot be joined. | segment_constraint_unsatisfied |

## P023 — Instrument suitability

Action query → available tools and typed affordances. Favor an applicable instrument.

**Status:** `table`. [Editable specification](data/P023.json).

Supply current, scoped records in channel available_tool. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P023.01 | Hammer is available and suitable for driving a nail. | `drive_nail` → `hammer` → `striking:1` | hammer / brush |
| P023.02 | Brush is available and suitable for painting. | `paint` → `brush` → `painting:1` | brush / hammer |
| P023.03 | Needle supports sewing cloth. | `sew` → `needle` → `stitching:1` | needle / spoon |
| P023.04 | Spoon supports stirring soup. | `stir` → `spoon` → `stirring:1` | spoon / needle |
| P023.05 | Scissors cut paper. | `cut_paper` → `scissors` → `cutting:1` | scissors / ladder |
| P023.06 | Ladder provides height. | `reach_shelf` → `ladder` → `reaching:1` | ladder / scissors |
| P023.07 | Lantern illuminates a dark space. | `illuminate` → `lantern` → `lighting:1` | lantern / bucket |
| P023.08 | Bucket carries water. | `carry_water` → `bucket` → `containing:1` | bucket / lantern |
| P023.09 | Screwdriver turns a screw. | `tighten_screw` → `screwdriver` → `turning:1` | screwdriver / tape |
| P023.10 | Tape patches a paper tear. | `patch_paper` → `tape` → `adhesion:1` | tape / screwdriver |

## P024 — Physical concept carrier

Concept-conditioned query → entities carrying that concept. Favor the carrier's manifestation; emit nothing from an unembedded concept.

**Status:** `program_required`. [Editable specification](data/P024.json).

**Raises `ProgramRequired`:** Bind concept magnitudes to real carrier entities and select manifestations using their state; reject bare/unembedded concepts.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P024.01 | Mira carries Fear=.8 after a growl. | carrier:Mira;fear:.8 |
| P024.02 | Theo carries Envy=.6 after Nia wins. | carrier:Theo;envy:.6 |
| P024.03 | An unattached Love label exists without a person or book. | zero_influence |
| P024.04 | Book contains a warning; nobody has read it. | book_carrier_only |
| P024.05 | Mira reads the warning and acquires caution. | distinct_reader_update_after_event |
| P024.06 | Two characters carry opposite amounts of Trust. | entity_specific_magnitudes |
| P024.07 | A carrier has been removed from the world. | invalid_carrier |
| P024.08 | Mira's Fear decreases after rescue. | current_lower_magnitude |
| P024.09 | One object physically embodies a community promise. | object_bound_concept |
| P024.10 | The requested concept is absent from every carrier. | abstain |

## P025 — Latest state override

Property query → ordered updates to that property. Favor current rather than stale state.

**Status:** `program_required`. [Editable specification](data/P025.json).

**Raises `ProgramRequired`:** Resolve competing property updates by event time and validity; preserve negation, retractions, and actual-versus-hypothetical branches.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P025.01 | Gate open, then Mira closes it. | closed |
| P025.02 | Cup empty, then Theo fills it. | full |
| P025.03 | Lamp lit, then wind extinguishes it. | unlit |
| P025.04 | Rope tied, then Nia unties it. | untied |
| P025.05 | Door locked, then an attempted unlock fails. | locked |
| P025.06 | Boat damaged, then repaired, then damaged again. | damaged_latest_event |
| P025.07 | A later report repeats an outdated open-gate claim. | world_state_not_overwritten_by_report |
| P025.08 | Two equal-time incompatible updates arrive. | conflict_requires_resolution |
| P025.09 | A hypothetical future repair has not happened. | retain_current_damage |
| P025.10 | An erroneous state event is explicitly retracted. | restore_last_valid_value |

## P026 — Precondition satisfaction

Action query → explicit prerequisites. Reweight success, failure, or preparation.

**Status:** `program_required`. [Editable specification](data/P026.json).

**Raises `ProgramRequired`:** Evaluate typed precondition expressions against persistent world state, returning missing prerequisites and their evidence rather than surface associations.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P026.01 | Lid fastened; opening requires unfastened. | missing:unfasten |
| P026.02 | Sack untied; opening requires untied. | prerequisites_met |
| P026.03 | Launch requires repaired boat and open water; only boat repaired. | missing:open_water |
| P026.04 | Lighting requires fuel and spark; both available. | prerequisites_met |
| P026.05 | Climbing requires strength or a ladder; ladder available. | disjunction_satisfied |
| P026.06 | Opening requires the right key, not merely any key. | missing:matching_key |
| P026.07 | Crossing requires a bridge that has not collapsed. | negated_precondition_failed |
| P026.08 | Recipe requires two eggs; only one exists. | quantity_precondition_failed |
| P026.09 | Required location is unknown. | precondition_unknown |
| P026.10 | Proposed action has no registered preconditions. | unsupported_action_contract |

## P027 — Causal-parent retrieval

Why-query or explanation → recorded cause edge. Favor an evidenced explanation.

**Status:** `program_required`. [Editable specification](data/P027.json).

**Raises `ProgramRequired`:** Follow recorded cause edges in the event graph, distinguish temporal neighbors from causes, and preserve multiple or unknown causes.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P027.01 | Gust pushes shutter; shutter slams. | cause:gust_event |
| P027.02 | Rope snaps; bucket falls. | cause:rope_break_event |
| P027.03 | Rain occurs before a letter arrives without a cause edge. | no_causal_link |
| P027.04 | Flood requires heavy rain plus blocked drain. | causes:{rain,blocked_drain} |
| P027.05 | Mira's warning causes Nia to stop. | cause:warning_event |
| P027.06 | Cup breaks accidentally but no cause is recorded. | cause_unknown |
| P027.07 | Theo blames Omar without supporting evidence. | attribution_not_world_cause |
| P027.08 | Fire causes smoke, which triggers alarm. Query alarm. | immediate:smoke;ancestor:fire |
| P027.09 | An imagined accident has hypothetical causes only. | branch_scoped_causes |
| P027.10 | Cause record points to a missing event. | invalid_provenance |

## P028 — Consequence retrieval

Event-focused continuation → recorded resulting changes. Favor consequences already supported by the world.

**Status:** `program_required`. [Editable specification](data/P028.json).

**Raises `ProgramRequired`:** Traverse committed event-to-state effect edges, distinguish direct effects from inferred possibilities, and respect later invalidation.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P028.01 | Spill soaks letter. | result:letter_wet |
| P028.02 | Repair seals leak. | result:boat_watertight |
| P028.03 | Gift transfers cup and raises gratitude. | results:{ownership,carrier_gratitude} |
| P028.04 | Warning is ignored and causes no recorded action. | no_invented_compliance |
| P028.05 | Lamp extinguished. | result:lamp_unlit |
| P028.06 | Window opened then immediately closed. | historical_open_effect_not_current_state |
| P028.07 | Door unlocks but does not open. | unlocked_not_open |
| P028.08 | Action fails before any effects execute. | no_success_effect |
| P028.09 | Two events share the same resulting state. | preserve_both_provenances |
| P028.10 | No effect metadata exists for the event. | result_unknown |

## P029 — Temporal precedence

Two-event query → before/after relations. Favor consistent ordering words.

**Status:** `program_required`. [Editable specification](data/P029.json).

**Raises `ProgramRequired`:** Resolve partial temporal orders and interval relations; compute transitive precedence while detecting contradictions and incomparability.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P029.01 | Lamp lit before Mira enters. | lighting_before_entry |
| P029.02 | Cup washed after drinking. | drinking_before_washing |
| P029.03 | A before B and B before C. | A_before_C |
| P029.04 | A and B happen simultaneously. | overlap_not_precedence |
| P029.05 | A before B and B before A. | temporal_cycle |
| P029.06 | One event is yesterday, one tomorrow. | yesterday_before_tomorrow |
| P029.07 | Two events have no connecting temporal evidence. | order_unknown |
| P029.08 | Mira arrived during Theo's watch. | contained_interval |
| P029.09 | An event occurs before midnight and another after. | handle_day_boundary |
| P029.10 | A flashback is narrated later but occurred earlier. | event_time_not_text_order |

## P030 — Duration compatibility

Ongoing event → start time and elapsed interval. Downweight implausibly immediate completion.

**Status:** `program_required`. [Editable specification](data/P030.json).

**Raises `ProgramRequired`:** Compare elapsed time with typed duration models, units, environmental conditions, and uncertainty; avoid treating duration estimates as certainties.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P030.01 | Paint applied one minute ago; drying typically takes hours. | unlikely_dry |
| P030.02 | Seeds planted this morning; maturity takes weeks. | unlikely_mature |
| P030.03 | Water boiled for the required interval. | duration_satisfied |
| P030.04 | Bread baked briefly in an unheated oven. | time_alone_insufficient |
| P030.05 | Snow melts faster in warm weather than freezing weather. | condition_dependent_duration |
| P030.06 | A journey took two hours across a midnight boundary. | elapsed:2_hours |
| P030.07 | Start time is unknown. | duration_unknown |
| P030.08 | An instant switch action has no long waiting interval. | immediate_effect_possible |
| P030.09 | One clock uses minutes and another seconds. | unit_conversion_required |
| P030.10 | Estimated drying interval is a range. | probability_over_completion |

## P031 — Simultaneous-event consistency

Action query → actor's overlapping commitments. Downweight incompatible simultaneous actions.

**Status:** `program_required`. [Editable specification](data/P031.json).

**Raises `ProgramRequired`:** Perform interval/resource conflict checks for each actor and instrument, allowing compatible concurrent actions and distinguishing sequential events.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P031.01 | Mira carries a chest with both hands and tries to thread a needle. | hand_conflict |
| P031.02 | Theo holds a ladder while someone climbs. | commitment_active |
| P031.03 | Nia walks while speaking. | compatible_concurrency |
| P031.04 | Omar sleeps while supposedly steering a boat. | incompatible_activity |
| P031.05 | One hammer is assigned to two simultaneous repairs. | instrument_conflict |
| P031.06 | Two repairs use different hammers. | no_instrument_conflict |
| P031.07 | Mira finishes carrying before opening a jar. | sequential_no_conflict |
| P031.08 | A character with one free hand carries a cup. | capacity_sufficient |
| P031.09 | Two events overlap only in uncertain time ranges. | uncertain_conflict |
| P031.10 | An interrupted task releases its reserved tool. | reservation_released |

## P032 — Undo and restoration

Current goal → reversible prior change and inverse action. Favor state-restoring actions.

**Status:** `table`. [Editable specification](data/P032.json).

Supply current, scoped records in channel reversible_change. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P032.01 | Undo a tie by untying. | `restore` → `tied` → `untie:1` | untied / tightened |
| P032.02 | Restore exposure by uncovering. | `restore` → `covered` → `uncover:1` | uncovered / covered |
| P032.03 | Undo closing by opening. | `restore` → `closed` → `open:1` | opened / closed |
| P032.04 | Undo locking with an unlock action; prerequisites still belong to the world. | `restore` → `locked` → `unlock:1` | unlocked / locked |
| P032.05 | Undo folding by unfolding. | `restore` → `folded` → `unfold:1` | unfolded / folded |
| P032.06 | Undo filling by emptying. | `restore` → `filled` → `empty:1` | emptied / filled |
| P032.07 | Undo raising by lowering. | `restore` → `raised` → `lower:1` | lowered / raised |
| P032.08 | Undo attaching by detaching. | `restore` → `attached` → `detach:1` | detached / attached |
| P032.09 | Undo wrapping by unwrapping. | `restore` → `wrapped` → `unwrap:1` | unwrapped / wrapped |
| P032.10 | Undo switching on by switching off. | `restore` → `switched_on` → `switch_off:1` | off / on |

## P033 — Active goal

Actor-focused continuation → unsatisfied goal record. Favor goal-relevant actions.

**Status:** `program_required`. [Editable specification](data/P033.json).

**Raises `ProgramRequired`:** Query actor-specific goal records, satisfaction predicates, priorities, and abandonment history; do not infer goals merely from adjacent nouns.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P033.01 | Mira wants her lost key and has not found it. | active:find_key |
| P033.02 | Theo wants to repair a sail; sail remains torn. | active:repair_sail |
| P033.03 | Nia found the ring she was seeking. | goal_satisfied |
| P033.04 | Omar abandons his plan to leave. | goal_inactive |
| P033.05 | Mira has urgent rescue and optional decorating goals. | rescue_higher_priority |
| P033.06 | Theo wants what Nia wants but goal content is unresolved. | unresolved_goal_reference |
| P033.07 | A narrator mentions a key with no character desire. | no_goal_inferred |
| P033.08 | Two characters seek different keys. | actor_specific_targets |
| P033.09 | A goal becomes impossible after its object is destroyed. | impossible_goal_flag |
| P033.10 | A completed goal is explicitly renewed. | new_goal_instance |

## P034 — Goal blocker

Active goal → recorded obstacle. Favor resolving or routing around the blocker.

**Status:** `program_required`. [Editable specification](data/P034.json).

**Raises `ProgramRequired`:** Join active goals to failed prerequisites, causal obstacles, and alternative routes; distinguish a real blocker from incidental negative facts.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P034.01 | Leaving requires a bridge; bridge broken. | blocker:broken_bridge |
| P034.02 | Water collection requires the well; well dry. | blocker:dry_well |
| P034.03 | Painting goal exists but unrelated cup is broken. | unrelated_fact_not_blocker |
| P034.04 | Two routes exist and only one is blocked. | alternative_route_available |
| P034.05 | Opening door requires missing key. | blocker:missing_key |
| P034.06 | Key recovered; prior key blocker resolved. | remove_stale_blocker |
| P034.07 | Rescue blocked by height and missing ladder. | linked_blocker_chain |
| P034.08 | Mira fears heights but physical route is available. | distinguish_emotional_from_physical_blocker |
| P034.09 | No plan specifies how a goal will be reached. | blocker_unknown |
| P034.10 | A supposed blocker is based only on a false belief. | belief_scoped_blocker |

## P035 — Plan frontier

Current plan → first eligible unfinished step. Favor an executable next step.

**Status:** `program_required`. [Editable specification](data/P035.json).

**Raises `ProgramRequired`:** Maintain a dependency graph of plan steps with completion/failure states; return the eligible frontier without leaking future execution.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P035.01 | Find wood, patch boat, launch; wood found. | eligible:patch_boat |
| P035.02 | Fetch flour, mix, bake; flour fetched. | eligible:mix |
| P035.03 | Two independent preparation steps are unfinished. | eligible:both |
| P035.04 | A later step is complete but its prerequisite is invalidated. | inconsistent_plan_state |
| P035.05 | Launch requires repair and weather check; repair done only. | eligible:weather_check |
| P035.06 | The first step failed and a fallback is registered. | eligible:fallback |
| P035.07 | All steps are complete. | plan_complete |
| P035.08 | Dependency graph contains a cycle. | plan_cycle_error |
| P035.09 | One completed task produces a resource needed by another. | resource_dependency_frontier |
| P035.10 | Actor abandons the plan. | no_active_frontier |

## P036 — Character-specific belief

Character viewpoint → their latest observation or report. Favor viewpoint-consistent statements.

**Status:** `program_required`. [Editable specification](data/P036.json).

**Raises `ProgramRequired`:** Maintain observer-indexed belief states updated only through witnessed events or reports; distinguish nested beliefs and world truth.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P036.01 | Mira sees key in drawer then leaves before it moves. | Mira_believes:drawer |
| P036.02 | Theo hears gate open before Nia closes it unseen. | Theo_believes:open |
| P036.03 | Nia watches the key move to a box. | Nia_believes:box |
| P036.04 | Omar receives a correction after an earlier false report. | belief_updated_by_correction |
| P036.05 | Two witnesses see different stages of a transfer. | distinct_belief_states |
| P036.06 | Mira knows Theo did not see the transfer. | second_order_belief |
| P036.07 | The narrator knows a secret no character knows. | narrator_not_character_knowledge |
| P036.08 | A character doubts an unreliable report. | uncertain_belief_distribution |
| P036.09 | An event is imagined rather than observed. | imagined_branch_not_belief_fact |
| P036.10 | No evidence reaches the character. | belief_unknown |

## P037 — Witness access

Knowledge query → visibility and presence at an event. Downweight unexplained knowledge.

**Status:** `program_required`. [Editable specification](data/P037.json).

**Raises `ProgramRequired`:** Evaluate perceptual/report access using event time, location, visibility, hearing, attention, and recorded communication paths.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P037.01 | Nia watches Mira hide the map. | visual_access |
| P037.02 | Omar sleeps when Theo leaves. | no_access |
| P037.03 | Mira stands behind an opaque wall during the transfer. | no_visual_access |
| P037.04 | Theo hears a bell from another room. | auditory_access |
| P037.05 | Nia receives a letter reporting the arrival. | report_access |
| P037.06 | Omar arrives after the object was hidden. | no_direct_access_to_hiding |
| P037.07 | A character sees a box but not its concealed contents. | partial_access |
| P037.08 | A distant observer sees movement but cannot identify the person. | uncertain_identity |
| P037.09 | An event happens while a character looks away. | attention_blocks_observation |
| P037.10 | Visibility metadata is absent. | access_unknown |

## P038 — Information source reliability

Conflicting report → source track record and directness. Reweight certainty and attribution.

**Status:** `program_required`. [Editable specification](data/P038.json).

**Raises `ProgramRequired`:** Combine source identity, directness, calibrated reliability history, and correlated reports; do not confuse confident language with truth.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P038.01 | Nia guesses the bridge is safe. | low_directness |
| P038.02 | Mira inspects the broken plank herself. | direct_observation |
| P038.03 | Three reports all repeat one rumor. | one_underlying_source |
| P038.04 | A trusted observer is uncertain about distance. | trust_does_not_erase_uncertainty |
| P038.05 | A formerly unreliable source provides verifiable evidence. | evidence_updates_reliability |
| P038.06 | Two direct witnesses disagree. | unresolved_conflict |
| P038.07 | A report predates a major storm. | stale_source_evidence |
| P038.08 | An anonymous message has no track record. | unknown_reliability |
| P038.09 | A precise measurement conflicts with a vague guess. | measurement_weight_higher |
| P038.10 | A narrator uses emphatic wording without evidence. | no_confidence_from_style_alone |

## P039 — Unresolved uncertainty

Factual question → competing supported possibilities. Favor hedging or investigation over invented certainty.

**Status:** `program_required`. [Editable specification](data/P039.json).

**Raises `ProgramRequired`:** Represent competing supported hypotheses, normalize their weights, track missing evidence, and update them without inventing absent possibilities.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P039.01 | Sound may be rain or footsteps with equal support. | rain:.5,footsteps:.5 |
| P039.02 | Either Mira or Theo has the spare key. | holder_ambiguous |
| P039.03 | One of three boxes contains the ring; no further evidence. | three_way_distribution |
| P039.04 | Fresh footprints favor footsteps over rain. | update_toward_footsteps |
| P039.05 | All proposed explanations are contradicted. | unknown_not_forced_choice |
| P039.06 | One hypothesis has two independent supporting observations. | increase_supported_weight |
| P039.07 | Two observations duplicate the same report. | avoid_double_counting |
| P039.08 | The question presupposes a cause that was never recorded. | cause_unknown |
| P039.09 | A direct inspection resolves the ambiguity. | collapse_to_observed_alternative |
| P039.10 | Uncertainty concerns time, not identity. | preserve_dimension_specific_uncertainty |

## P040 — Promise obligation

Actor action query → active commitments to others. Favor fulfillment or explicitly motivated breach.

**Status:** `program_required`. [Editable specification](data/P040.json).

**Raises `ProgramRequired`:** Track promise events and their promisor, beneficiary, content, deadline, release, fulfillment, and conflicts with other obligations.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P040.01 | Mira promises Nia to return the cup by dusk. | obligation:return_cup;deadline:dusk |
| P040.02 | Theo agrees to watch until dawn. | watch_interval_obligation |
| P040.03 | Nia releases Mira from a promise. | obligation_cancelled |
| P040.04 | A promised cup is returned on time. | obligation_fulfilled |
| P040.05 | Deadline passes without fulfillment. | obligation_overdue |
| P040.06 | An actor merely hopes to help, without promising. | goal_not_promise |
| P040.07 | Two promises require incompatible simultaneous actions. | obligation_conflict |
| P040.08 | Promise is conditional on good weather; weather is bad. | condition_unsatisfied |
| P040.09 | A person promises on behalf of someone without authority. | disputed_obligation |
| P040.10 | A character intentionally breaks a promise. | breach_event_required_not_silent_relabeling |

## P041 — Speaker continuity

Quote continuation → current turn's speaker. Resolve first-person references consistently.

**Status:** `program_required`. [Editable specification](data/P041.json).

**Raises `ProgramRequired`:** Maintain a quotation/turn stack and speaker bindings, including nested quotations and reported speech; bind first person to the active speaker.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P041.01 | Mira says I will return. | I:Mira |
| P041.02 | Theo whispers my key is missing. | my:Theo |
| P041.03 | Nia quotes Omar saying I won. | inner_I:Omar |
| P041.04 | Mira narrates that Theo said I am ready. | quoted_I:Theo |
| P041.05 | An unattributed quotation has two possible speakers. | speaker_ambiguous |
| P041.06 | A dialogue turn explicitly switches from Mira to Nia. | active_speaker:Nia |
| P041.07 | A single quote spans two sentences. | speaker_persists |
| P041.08 | A character reads another person's diary aloud. | distinguish_reader_from_quoted_author |
| P041.09 | A closing quotation returns to narration. | pop_speaker_scope |
| P041.10 | An unclosed quotation reaches end of input. | preserve_open_turn_without_guessing_end |

## P042 — Addressee resolution

Second-person reference → intended listener. Bind second-person descriptions.

**Status:** `program_required`. [Editable specification](data/P042.json).

**Raises `ProgramRequired`:** Resolve dialogue addressees from turn metadata, vocatives, group address, and nested quotations; retain ambiguity when not established.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P042.01 | Mira tells Nia you should rest. | you:Nia |
| P042.02 | Theo asks Omar about your boat. | your:Omar |
| P042.03 | Mira addresses both Nia and Omar as you. | group_addressee |
| P042.04 | A speaker talks to herself. | addressee_equals_speaker |
| P042.05 | Omar, could you help? appears as a vocative. | addressee:Omar |
| P042.06 | A quoted letter addresses someone absent. | letter_recipient_not_listener |
| P042.07 | Two listeners are present without a selected addressee. | ambiguous_addressee |
| P042.08 | A new turn redirects a question to Theo. | addressee_updates |
| P042.09 | Generic you occurs in a proverb. | generic_not_entity_specific |
| P042.10 | A nested quote changes its own addressee. | nested_scope_binding |

## P043 — Question-answer focus

Reply → unresolved question slot. Favor an answer to the actual question.

**Status:** `program_required`. [Editable specification](data/P043.json).

**Raises `ProgramRequired`:** Parse question focus into entity/event and requested role, maintain unresolved slots, and retrieve only answerable world/trace facts.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P043.01 | Where is the lantern? Its current location is porch. | requested:location;answer:porch |
| P043.02 | Who moved the crate? Theo moved it. | requested:actor;answer:Theo |
| P043.03 | Why did the cup fall? Rope break is recorded as cause. | requested:cause;answer:rope_break |
| P043.04 | Which key opens the chest? Only brass key matches. | requested:instrument;answer:brass_key |
| P043.05 | How many boards remain? Inventory contains two. | requested:quantity;answer:2 |
| P043.06 | When did Mira leave? No time is recorded. | unanswerable_time |
| P043.07 | What happened next? follows a referenced rescue event. | next_event_after_rescue |
| P043.08 | Where? follows discussion of the key, not the lamp. | preserve_question_focus:key |
| P043.09 | Did Nia see the move? Witness record says no. | requested:access;answer:no |
| P043.10 | Who and where? asks two slots at once. | multi_slot_question |

## P044 — Adjacency-pair expectation

Reply → previous speech act. Favor acceptance/refusal or acknowledgment.

**Status:** `table`. [Editable specification](data/P044.json).

Supply current, scoped records in channel previous_speech_act. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P044.01 | A help request invites acceptance or refusal; this row favors acceptance. | `reply` → `request_help` → `accept_or_refuse:1` | Yes / Goodbye |
| P044.02 | Thanks invites acknowledgment. | `reply` → `thanks` → `acknowledge:1` | Welcome / Why |
| P044.03 | A greeting invites a reciprocal greeting. | `reply` → `greeting` → `greet_back:1` | Hello / Because |
| P044.04 | An apology can receive acceptance. | `reply` → `apology` → `accept_apology:1` | Okay / Hello |
| P044.05 | An invitation can receive willing acceptance. | `reply` → `invitation` → `accept_invitation:1` | Gladly / Because |
| P044.06 | A farewell can receive a farewell. | `reply` → `farewell` → `farewell_back:1` | Goodbye / Why |
| P044.07 | A polar question can receive no. | `reply` → `yes_no_question` → `answer_polarity:1` | No / Welcome |
| P044.08 | A why question invites explanation. | `reply` → `why_question` → `explain:1` | Because / Goodbye |
| P044.09 | An offer can receive gratitude. | `reply` → `offer` → `accept_offer:1` | Thanks / Where |
| P044.10 | A warning invites acknowledgment. | `reply` → `warning` → `acknowledge_warning:1` | Understood / Welcome |

## P045 — Conversation repair

Current turn → disputed or corrected phrase. Favor the corrected referent.

**Status:** `program_required`. [Editable specification](data/P045.json).

**Raises `ProgramRequired`:** Track explicit conversational corrections and their scope, replacing disputed bindings while preserving who asserted each version.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P045.01 | The red cup? No, the blue one. | referent:blue_cup |
| P045.02 | At noon? I meant dusk. | corrected_time:dusk |
| P045.03 | Mira says Theo came; Nia corrects it to Omar. | corrected_actor:Omar |
| P045.04 | Correction is itself retracted. | restore_previous_supported_binding |
| P045.05 | Not the big box, the small box. | size_constraint:small |
| P045.06 | Correction refers to quoted speech rather than world truth. | quote_scoped_correction |
| P045.07 | Two listeners reject different parts of a claim. | partial_corrections |
| P045.08 | No, I meant she brought it, not took it. | corrected_event_direction |
| P045.09 | A sarcastic no is not a factual correction. | require_speech_act_disambiguation |
| P045.10 | Correction names an entity not previously introduced. | new_binding_requires_grounding |

## P046 — Shared knowledge

Explanatory turn → overlap in interlocutors' knowledge. Reweight reminders versus explanations.

**Status:** `program_required`. [Editable specification](data/P046.json).

**Raises `ProgramRequired`:** Compute conversation common ground from participant-specific knowledge and acknowledgments; distinguish mutual knowledge from mere coincident beliefs.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P046.01 | Both watched the bridge collapse together. | shared_observation |
| P046.02 | Only Mira saw the crack. | listener_gap:crack |
| P046.03 | Theo tells Nia the key location and she acknowledges. | common_ground_updated |
| P046.04 | Theo reports a fact but Nia cannot hear. | no_shared_update |
| P046.05 | Both know a fact but neither knows the other knows. | not_mutually_established |
| P046.06 | A new listener joins halfway through. | new_listener_gaps |
| P046.07 | A previously shared fact becomes false after an unseen event. | shared_belief_not_current_truth |
| P046.08 | One listener disputes a claim. | contested_common_ground |
| P046.09 | A secret is deliberately withheld from Omar. | Omar_excluded |
| P046.10 | No participant knowledge records exist. | common_ground_unknown |

## P047 — Speech intention

Dialogue continuation → speaker's communicative goal. Favor warning or apology language.

**Status:** `table`. [Editable specification](data/P047.json).

Supply current, scoped records in channel communicative_goal. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Positive relative word-weight multipliers.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P047.01 | Ice hazard goal favors a warning. | `utterance` → `warn_ice` → `warning:1` | Careful / Congratulations |
| P047.02 | Spill apology favors sorry. | `utterance` → `apologize_spill` → `apology:1` | Sorry / Hooray |
| P047.03 | Key request favors please. | `utterance` → `request_key` → `request:1` | Please / Farewell |
| P047.04 | Helping acknowledgment favors thank. | `utterance` → `thank_help` → `gratitude:1` | Thank / Beware |
| P047.05 | Meal invitation favors join. | `utterance` → `invite_meal` → `invitation:1` | Join / Stop |
| P047.06 | Reassurance favors safe when supported by the world. | `utterance` → `reassure_child` → `reassurance:1` | Safe / Danger |
| P047.07 | Refusal intention favors no. | `utterance` → `refuse_offer` → `refusal:1` | No / Certainly |
| P047.08 | Success acknowledgment favors congratulations. | `utterance` → `congratulate_success` → `congratulation:1` | Congratulations / Sorry |
| P047.09 | Location inquiry favors where. | `utterance` → `ask_location` → `location_question:1` | Where / When |
| P047.10 | Reason inquiry favors why. | `utterance` → `ask_reason` → `reason_question:1` | Why / Who |

## P048 — Turn-taking

Next utterance → previous turn and response obligation. Favor a relevant respondent.

**Status:** `program_required`. [Editable specification](data/P048.json).

**Raises `ProgramRequired`:** Maintain turn order, explicit floor allocation, pending response obligations, interruptions, and multi-party ambiguity.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P048.01 | Mira asks Theo a question. | next_candidate:Theo |
| P048.02 | Nia invites Omar to explain. | next_candidate:Omar |
| P048.03 | A greeting addresses a whole group. | multiple_respondents_possible |
| P048.04 | Theo is interrupted by Mira before answering. | interruption_then_pending_answer |
| P048.05 | No one is asked a question after a statement. | open_floor |
| P048.06 | A speaker explicitly continues her own story. | same_speaker_allowed |
| P048.07 | Omar leaves before his response turn. | unavailable_respondent |
| P048.08 | Two speakers volunteer simultaneously. | competing_turn_claims |
| P048.09 | A rhetorical question needs no answer. | no_response_obligation |
| P048.10 | An earlier unanswered request remains pending. | preserve_pending_obligation |

## P049 — Premise completion

Opening → missing participant/place/problem slots. Favor completing the premise.

**Status:** `program_required`. [Editable specification](data/P049.json).

**Raises `ProgramRequired`:** Track which premise slots are already grounded in the narrative/world and choose missing introductions without inventing a problem or duplicating exposition.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P049.01 | Mira arrived at the mill; no problem established. | missing:problem |
| P049.02 | Village well is dry; no actor introduced. | missing:actor |
| P049.03 | Actor and problem exist but place is unspecified. | missing:place |
| P049.04 | Actor, setting, and problem are all present. | premise_complete |
| P049.05 | A new scene changes place without an introduction. | scene_location_gap |
| P049.06 | Problem is only mentioned in a hypothetical tale. | actual_premise_still_missing |
| P049.07 | Two actors are introduced but their relationship matters and is absent. | missing:relevant_relationship |
| P049.08 | Opening describes weather without a protagonist or problem. | missing:{actor,problem} |
| P049.09 | A terse opening already implies a grounded danger. | avoid_redundant_problem_restatement |
| P049.10 | No valid world event can supply a missing premise. | request_more_world_state_not_fabricated_text |

## P050 — Unresolved-thread retrieval

Scene continuation → salient unfinished event. Favor returning to a live thread.

**Status:** `program_required`. [Editable specification](data/P050.json).

**Raises `ProgramRequired`:** Maintain persistent narrative threads with event IDs, resolution predicates, salience, scene relevance, and explicit abandonment.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P050.01 | Strange knock has not been answered. | live_thread:knock |
| P050.02 | Missing ring remains unfound. | live_thread:ring |
| P050.03 | Knock is answered and visitor identified. | thread_resolved |
| P050.04 | Two mysteries remain with different urgency. | ranked_live_threads |
| P050.05 | A promise is forgotten in narration but not fulfilled. | obligation_thread_remains |
| P050.06 | A red herring is explicitly dismissed. | thread_closed |
| P050.07 | Scene changes but a critical danger persists. | carry_thread_across_scene |
| P050.08 | A repeated description creates no new event. | no_duplicate_thread |
| P050.09 | A character abandons a search with an explicit reason. | thread_abandoned |
| P050.10 | No unresolved event exists. | no_thread_signal |

## P051 — Emotional cause continuity

Actor description → emotion-changing events. Favor a state-consistent reaction.

**Status:** `program_required`. [Editable specification](data/P051.json).

**Raises `ProgramRequired`:** Read carrier-bound emotion updates and their causal provenance, with decay, intervening events, and mixed emotions.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P051.01 | Growl raises Mira's fear. | Mira:fear;cause:growl |
| P051.02 | Recovering keepsake relieves Theo. | Theo:relief;cause:recovery |
| P051.03 | Nia feels joy and grief at a farewell. | mixed_emotions |
| P051.04 | Fear fades after danger is removed. | current_reduced_fear |
| P051.05 | Another character's sadness is described nearby. | do_not_transfer_carrier |
| P051.06 | Emotion is quoted from a diary about yesterday. | historical_emotion_scope |
| P051.07 | No cause is recorded for an emotion. | emotion_known_cause_unknown |
| P051.08 | Repeated help gradually raises trust. | accumulated_carrier_state |
| P051.09 | An abstract fear concept has no physical carrier. | zero_influence |
| P051.10 | A later betrayal reverses earlier relief. | latest_emotional_update |

## P052 — Emotion regulation

Actor action → current emotion and learned coping behavior. Favor grounded changes in emotional state.

**Status:** `program_required`. [Editable specification](data/P052.json).

**Raises `ProgramRequired`:** Match available coping actions to a carrier emotion and learned history, checking prerequisites and updating emotions only on committed events.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P052.01 | Mira is afraid and remembers slow breathing. | available_coping:breathing |
| P052.02 | Theo is angry and can step outside. | available_coping:distance |
| P052.03 | Nia seeks a trusted friend after grief. | available_coping:social_support |
| P052.04 | Omar has no learned calming strategy. | no_invented_strategy |
| P052.05 | A suggested coping action is physically unavailable. | exclude_infeasible_coping |
| P052.06 | Breathing is considered but not yet performed. | fear_not_yet_reduced |
| P052.07 | A prior coping attempt failed. | revise_expected_effect |
| P052.08 | A strategy learned by Mira is unknown to Theo. | carrier_specific_knowledge |
| P052.09 | Joy needs no forced calming response. | no_problem_assumed |
| P052.10 | Two coping strategies have uncertain benefit. | distribution_over_actions |

## P053 — Relationship-specific behavior

Interaction → pair's accumulated relationship state. Reweight disclosure, cooperation, or caution.

**Status:** `program_required`. [Editable specification](data/P053.json).

**Raises `ProgramRequired`:** Query directed pair-specific relationship magnitudes and history, then gate behavioral priors by actor, partner, and compatible commitments.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P053.01 | Mira trusts Nia after repeated help. | Mira_to_Nia:high_trust |
| P053.02 | Theo distrusts Omar after a broken promise. | Theo_to_Omar:low_trust |
| P053.03 | Nia trusts Mira but Mira does not trust Nia. | directed_relationship |
| P053.04 | Two people share a name but have different histories. | bind_pair_by_ids |
| P053.05 | A stranger has no relationship record. | unknown_relationship |
| P053.06 | Reconciliation improves a previously damaged bond. | updated_relationship |
| P053.07 | Envy is high despite affection. | mixed_relationship_dimensions |
| P053.08 | Trust in one skill does not imply trust in every domain. | domain_scoped_trust |
| P053.09 | A coercive obligation conflicts with friendly behavior. | preserve_conflicting_constraints |
| P053.10 | An imagined friendship has no carrier-bound state. | no_real_relationship_update |

## P054 — State-driven turning point

Narrative midpoint → a change enabling a previously blocked option. Favor a consequential turn.

**Status:** `program_required`. [Editable specification](data/P054.json).

**Raises `ProgramRequired`:** Compare before/after world states and action eligibility to find consequential enabling changes, rather than choosing dramatic wording by keyword.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P054.01 | Found key unlocks the only exit. | newly_enabled:escape |
| P054.02 | Nia arrives with the missing repair skill. | newly_enabled:repair |
| P054.03 | Lamp is relit but the key was already visible. | not_a_new_enabler |
| P054.04 | Bridge repair connects previously separated banks. | newly_enabled:crossing |
| P054.05 | A revelation changes belief but not physical possibility. | epistemic_turn |
| P054.06 | An apparent solution fails to remove the blocker. | false_turn |
| P054.07 | Two simultaneous changes are jointly required for rescue. | joint_enabling_change |
| P054.08 | Removing a resource closes options instead of opening them. | setback_turn |
| P054.09 | A cosmetic color change leaves options unchanged. | weak_turn |
| P054.10 | A proposed future repair has not occurred. | no_committed_turn |

## P055 — Resolution verification

Closing passage → initial goal and present world state. Favor closure only when supported.

**Status:** `program_required`. [Editable specification](data/P055.json).

**Raises `ProgramRequired`:** Evaluate initial goals and active conflicts against terminal state, preserving partial success, failure, sacrifice, and unresolved obligations.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P055.01 | Repaired boat carries everyone home. | rescue_goal_satisfied |
| P055.02 | Lost child reunites safely with family. | reunion_goal_satisfied |
| P055.03 | Key found but door remains locked. | partial_resolution |
| P055.04 | One traveler is still stranded. | unresolved_rescue |
| P055.05 | Goal is abandoned after a meaningful change of values. | explicit_goal_revision |
| P055.06 | A success claim contradicts current damaged state. | false_resolution |
| P055.07 | Task succeeded but a return promise remains unfulfilled. | residual_obligation |
| P055.08 | Attempt fails and the story acknowledges the loss. | grounded_failure_ending |
| P055.09 | No initial goal was established. | resolution_reference_missing |
| P055.10 | Physical goal succeeds at a relationship cost. | mixed_outcome |

## P056 — Final-image selection

Ending → concrete objects whose states show the change. Favor an ending image that demonstrates the outcome.

**Status:** `program_required`. [Editable specification](data/P056.json).

**Raises `ProgramRequired`:** Select grounded physical carriers whose before/after states express the resolved change, with viewpoint and visibility checks.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P056.01 | Broken lantern now lights the doorstep. | image:lit_lantern |
| P056.02 | Once-empty bench now holds both friends. | image:occupied_bench |
| P056.03 | Torn sail now carries the boat forward. | image:working_sail |
| P056.04 | Dry garden now contains watered seedlings. | image:watered_plants |
| P056.05 | Borrowed cup rests back on its owner's shelf. | image:returned_cup |
| P056.06 | Locked door now stands open. | image:open_door |
| P056.07 | A purely abstract happiness label lacks a carrier. | reject_bare_concept_image |
| P056.08 | Proposed final image shows a repair that never happened. | reject_ungrounded_image |
| P056.09 | Changed object exists but viewpoint cannot observe it. | visibility_constraint |
| P056.10 | Story ends in loss with an empty chair. | grounded_negative_final_image |

## P057 — Predicate-filtered retrieval

Query predicate → matching past items only. Favor continuations grounded in the selected subset.

**Status:** `program_required`. [Editable specification](data/P057.json).

**Raises `ProgramRequired`:** Evaluate typed predicates over a dynamic candidate set, preserving conjunction, negation, missing values, and selection weights.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P057.01 | Red cup and blue bowl; select red. | {red_cup} |
| P057.02 | Small box and large crate; select large. | {large_crate} |
| P057.03 | Three tools; select portable and metal. | conjunction_matches_only |
| P057.04 | One object has unknown color; select red. | unknown_not_false_certainty |
| P057.05 | Select objects not broken. | negation_with_known_states |
| P057.06 | No candidate satisfies the predicate. | empty_selection |
| P057.07 | Several cups satisfy red. | preserve_all_matches |
| P057.08 | Predicate concerns owner rather than appearance. | typed_relation_filter |
| P057.09 | The same object appears twice in memory. | deduplicate_by_entity_id |
| P057.10 | Filter refers to an unsupported attribute. | unsupported_predicate |

## P058 — Abstract-role transfer

Current relation pattern → analogous earlier role mapping. Favor the same role rather than the same surface token.

**Status:** `program_required`. [Editable specification](data/P058.json).

**Raises `ProgramRequired`:** Align relational frame roles across examples using variable bindings and type constraints, distinguishing role transfer from surface-token copying.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P058.01 | Mira gives Nia cup; Theo gives Omar map; ask recipient. | Omar |
| P058.02 | Bird carries twig; child carries rope; ask carrier. | child |
| P058.03 | Nia lends Theo key; Omar lends Mira book; ask lender. | Omar |
| P058.04 | Door opened with key; crate opened with crowbar; ask instrument. | crowbar |
| P058.05 | Mira follows Nia; Theo follows Omar; ask leader. | Omar |
| P058.06 | Same names occur with reversed giver/recipient roles. | respect_role_not_name_order |
| P058.07 | Passive sentence reverses surface order but preserves agent. | agent_binding |
| P058.08 | One frame lacks a required role. | incomplete_alignment |
| P058.09 | Two roles can align equally well. | ambiguous_mapping |
| P058.10 | Analogy proposes an entity absent from the second frame. | reject_unbound_value |

## P059 — Conditional continuation counts

Current word and active feature → matching corpus contexts. Apply a smoothed empirical probability adjustment.

**Status:** `table`. [Editable specification](data/P059.json).

Supply current, scoped records in channel active_context_feature. Scope selection and structural parsing belong to the caller; no free-text parser is implied.

Illustrative continuation counts, smoothed toward the grammar distribution.

| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |
| --- | --- | --- | --- |
| P059.01 | River with water favors flows; sings remains possible with lower count. | `river` → `water` → `water:1` | flows / sings |
| P059.02 | Bird with song favors sings. | `bird` → `song` → `song:1` | sings / flows |
| P059.03 | Fire with heat favors burns. | `fire` → `heat` → `heat:1` | burns / freezes |
| P059.04 | Snow with cold favors falls. | `snow` → `cold` → `cold:1` | falls / burns |
| P059.05 | Locked door favors resists over unsupported opens. | `door` → `locked` → `locked:1` | resists / opens |
| P059.06 | Unlocked door reverses the contextual preference. | `door` → `unlocked` → `unlocked:1` | opens / resists |
| P059.07 | Seed with moisture favors sprouts. | `seed` → `moisture` → `moisture:1` | sprouts / rusts |
| P059.08 | The same moisture feature has a different effect with iron. | `iron` → `moisture` → `moisture:1` | rusts / sprouts |
| P059.09 | A fear feature favors hesitation for child. | `child` → `fear` → `fear:1` | hesitates / celebrates |
| P059.10 | A joy feature changes the child continuation. | `child` → `joy` → `joy:1` | celebrates / hesitates |

## P060 — Counterevidence retrieval

Candidate claim → facts inconsistent with it. Reduce unsupported candidates without automatically forbidding them.

**Status:** `program_required`. [Editable specification](data/P060.json).

**Raises `ProgramRequired`:** Evaluate candidate claims against typed world constraints and scoped evidence, with contradiction strength and modal/negation handling.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P060.01 | Candidate entered easily; door locked with no key. | physical_counterevidence |
| P060.02 | Candidate thanked warmly; trust collapsed after betrayal. | behavioral_counterevidence_not_absolute_ban |
| P060.03 | Candidate cup is full; cup was just emptied. | state_contradiction |
| P060.04 | Candidate Mira knows secret; she had no access. | knowledge_counterevidence |
| P060.05 | Candidate maybe the cup is full; contents unknown. | uncertainty_not_contradiction |
| P060.06 | Candidate quotes a false claim rather than asserting it. | quotation_scope |
| P060.07 | Candidate gate is not open; gate is closed. | compatible_negation |
| P060.08 | Evidence concerns a different cup. | reject_wrong_entity_counterevidence |
| P060.09 | An older fact contradicts a newer valid state. | stale_fact_not_counterevidence |
| P060.10 | Two valid facts conflict. | unresolved_world_conflict |

## P061 — Evidence freshness

Retrieved fact → age and intervening relevant events. Discount stale evidence.

**Status:** `program_required`. [Editable specification](data/P061.json).

**Raises `ProgramRequired`:** Compute evidence age relative to query time and invalidate it through intervening relevant events; use property-specific persistence models.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P061.01 | Bridge inspected before a severe storm. | inspection_stale |
| P061.02 | Latch tested after repair. | fresh_evidence |
| P061.03 | Birth date recorded long ago. | stable_property_not_time_decayed |
| P061.04 | Cup location recorded before it was moved. | invalidated_location |
| P061.05 | Weather report is a week old. | low_freshness |
| P061.06 | An event has no timestamp but known ordering. | partial_temporal_freshness |
| P061.07 | Two reports refer to the same observation time. | same_age_despite_report_order |
| P061.08 | A later message repeats an old inspection. | do_not_refresh_observation_time |
| P061.09 | An object state persists without intervening changes. | persistence_support |
| P061.10 | Query asks historical state at yesterday noon. | freshness_relative_to_query_time |

## P062 — Correlated-evidence discount

Active features → shared supporting event IDs. Avoid counting the same evidence three times.

**Status:** `program_required`. [Editable specification](data/P062.json).

**Raises `ProgramRequired`:** Group activations by shared provenance and estimate dependence before combining scores; do not treat different feature names as independent evidence.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P062.01 | One gift activates kindness, gratitude, friendship. | one_shared_event_group |
| P062.02 | One warning activates danger, fear, caution. | one_shared_event_group |
| P062.03 | Two independent witnesses observe the same event. | distinguish_observation_independence_from_event_identity |
| P062.04 | Three reports repeat one rumor. | correlated_report_group |
| P062.05 | Two unrelated gifts occur on separate days. | separate_evidence_groups |
| P062.06 | Two heads read the same token and produce equivalent features. | redundant_activation_group |
| P062.07 | One head reads event cause and another its effect. | causal_dependence |
| P062.08 | Provenance IDs are missing. | dependence_unknown |
| P062.09 | Different source IDs are aliases of one record. | canonicalize_provenance |
| P062.10 | One source supports both compatible and opposing hypotheses. | preserve_signed_contributions |

## P063 — Sparse-context backoff

Feature-conditioned predictor → effective sample support. Back off toward grammar/base statistics when evidence is sparse.

**Status:** `program_required`. [Editable specification](data/P063.json).

**Raises `ProgramRequired`:** Estimate effective sample support and fit hierarchical interpolation between trigram, bigram, and grammar priors; account for correlated counts.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P063.01 | Recipient trigram has one observation. | strong_backoff |
| P063.02 | Locked-door feature has hundreds of independent observations. | weaker_backoff |
| P063.03 | Trigram absent but bigram has support. | backoff_to_bigram |
| P063.04 | Neither trigram nor bigram has support. | grammar_prior |
| P063.05 | Large counts duplicate one repeated document. | reduced_effective_support |
| P063.06 | New domain differs from the counting corpus. | domain_shift_discount |
| P063.07 | Frequent context has highly variable continuations. | preserve_entropy |
| P063.08 | Rare context has one extreme outlier. | shrink_outlier |
| P063.09 | Counts include held-out evaluation text. | reject_leakage |
| P063.10 | Support is unknown for an authored multiplier table. | do_not_fabricate_sample_count |

## P064 — Null-evidence abstention

Query → whether any supported source exists. Apply no factual boost; favor supported uncertainty where appropriate.

**Status:** `program_required`. [Editable specification](data/P064.json).

**Raises `ProgramRequired`:** Determine whether required evidence is genuinely absent, contradicted, unavailable, or unparsed; decide when to communicate uncertainty rather than merely emitting no score.

| Example | Context | Intended feature (not implemented) |
| --- | --- | --- |
| P064.01 | No key location has been established. | location_unknown |
| P064.02 | No cause recorded for a noise. | cause_unknown |
| P064.03 | A head has no lexical table entry for a known fact. | coverage_gap_not_world_unknown |
| P064.04 | Two reports conflict about ownership. | conflict_not_absence |
| P064.05 | Knowledge exists but is hidden from the viewpoint. | viewpoint_unknown |
| P064.06 | All source confidences are zero. | no_usable_evidence |
| P064.07 | A source is excluded by the wrong scope. | scope_mismatch |
| P064.08 | The grammar has no legal candidates. | grammar_failure_not_factual_uncertainty |
| P064.09 | An unknown amount is explicitly recorded. | known_unknown_quantity |
| P064.10 | New evidence resolves an earlier unknown. | stop_abstaining |


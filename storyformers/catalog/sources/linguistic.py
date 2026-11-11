"""256 proposed linguistic dimensions with linked grammar/head hypotheses.

The executable rules are deliberately small seed recognizers. Larger syntactic
operations are explicit adapter contracts; none silently invokes a parser.
"""

import re

from ..schema import Catalog, example, gap, neuron, one_of, present, ref, seq, tok


SOURCES = ("gf.reference", "gf.rgl", "codeco", "ace", "local.storyformer")


def words(text):
    return [{"token": token} for token in re.findall(r"\w+(?:['’]\w+)?|[^\w\s]", text)]


def build():
    c = Catalog("linguistic", 257)

    def native(key, type, description, family, value, pattern, positive, negative,
               *, emit=None, tables=None, scope="current linguistic unit", notes=""):
        c.add(key, type, description, family, value=value, scope=scope,
              head="derive_" + key,
              function=f"Recognize the stated prefix evidence and project {key}: {description}",
              mechanism="weighted_pattern_and_projection",
              positive=example(positive, {key: value}, "The current prefix supplies this construction's stated evidence."),
              negative=example(negative, {}, "The contrasting prefix lacks the required construction evidence; abstain."),
              native=neuron(pattern, emit or {key: value}, tables=tables), sources=SOURCES,
              notes=(notes + " This executable seed has finite coverage; the field definition is broader than this one seed.").strip())

    def lex(key, type, description, family, mapping, pos, contrast, *, scope="current token", notes=""):
        # Keep the repository's compact POS vocabulary. More specific syntax is
        # a separate feature, never a new spelling of POS.
        pos = {"prep": "adp", "particle": "part", "aux": "v", "comp": "conj",
               "subord": "conj", "predet": "det", "clitic": "part",
               "rel": "pron", "punct": "unknown"}.get(pos, pos)
        gates = {"relative_marker_form": {"clause_type": "relative"},
                 "interrogative_complementizer": {"clause_type": "embedded_interrogative"}}.get(key, {})
        pos_test = pos
        if key == "negation_marker_form":
            pos, pos_test = "part", one_of("part", "adv")
        if key == "clause_speech_form":
            # Prefix annotation synthesizes punctuation outside the LLM POS enum.
            pos, pos_test = "punct", one_of("punct", "unknown")
        first, value = next(iter(mapping.items()))
        contrast_token, contrast_pos = contrast if isinstance(contrast, tuple) else (contrast, pos)
        native(key, type, description, family, value,
               seq(gap(), tok("cue", token=one_of(*mapping), pos=pos_test, **gates)),
               [{"token": first, "pos": pos, **gates}], [{"token": contrast_token, "pos": contrast_pos, **gates}],
               emit={key: {"$lookup": {"table": "forms", "key": ref("cue.token")}}},
               tables={"forms": mapping}, scope=scope, notes=notes)

    def pair(key, type, description, family, left, right, value, contrast,
             *, left_pos=None, right_pos=None, scope="current construction", notes=""):
        lt, rt = {"token": left}, {"token": right}
        if left_pos:
            lt["pos"] = left_pos
        if right_pos:
            rt["pos"] = right_pos
        negative = [dict(lt), {**rt, "token": contrast}]
        native(key, type, description, family, value, seq(gap(), tok(**lt), tok(**rt)),
               [lt, rt], negative, scope=scope, notes=notes)

    def contract(key, type, description, family, value, positive, negative, construction,
                 computation, *, guard, requires=("incremental_constituent_analysis", "deterministic_syntax_node_ids"),
                 scope="current construction", reads=("token", "pos"), notes=""):
        positive_context = words(positive)
        if type == "entity_ref":
            referent_words = {"grammatical_object_id": "box", "indirect_object_id": "Ben",
                              "prepositional_object_id": "Ben", "subject_controller_id": "Lily",
                              "object_controller_id": "Ben", "shared_subject_id": "Lily",
                              "shared_object_id": "book"}
            for record in positive_context:
                if record["token"] == referent_words[key]:
                    record["entity_id"] = value
            reads = tuple(reads) + ("entity_id",)
        c.add(key, type, description, family, value=value, scope=scope,
              head="resolve_" + key,
              function=f"For {construction}, {computation}; project the result as {key}.",
              mechanism="typed_construction_resolution",
              positive=example(positive_context, {key: value}, f"The visible prefix licenses {construction}; the projected value is a hypothesis at its final token."),
              negative=example(words(negative), {}, f"The contrast does not establish {construction}; retain unknown instead of inventing a value."),
              contract={
                  "match": {"construction": construction, "input": "visible_prefix",
                            "bind": {"query": "last visible token", "unit": "construction ending at or containing query",
                                     "analysis": "compatible incremental parse candidate"}},
                  "guards": ["All evidence and bindings precede or coincide with query.", guard,
                             "Preserve separate analyses when the prefix is syntactically ambiguous."],
                  "emit": {key: {"compute": computation, "from": ["analysis", "unit", "query"]}},
                  "write_target": "query",
              }, requires=requires, reads=reads, sources=SOURCES,
              notes=(notes + " Token anchors tN are one-based within the invented example; NP/VP/clause IDs are schematic parser handles. A concrete adapter must allocate stable IDs from visible structure.").strip())

    # 1. Constituent state: typed partial analyses, not token classes.
    f = "constituent_state"
    pair("constituent_category", "string", "Syntactic category of a constituent whose head is the current token.", f,
         "the", "rabbit", "NP", "quickly", notes="The seed identifies a simple determiner–noun phrase, without choosing a discourse referent.")
    native("constituent_head_id", "entity_ref", "Entity-denoting head of the current simple phrase, when an entity ID is already grounded.", f,
           "e1", seq(tok("head", token="Lily", pos="n", entity_id=present()), tok(token="herself")),
           [{"token": "Lily", "pos": "n", "entity_id": "e1"}, {"token": "herself"}],
           [{"token": "Lily", "pos": "n"}, {"token": "herself"}], emit={"constituent_head_id": ref("head.entity_id")},
           notes="Intensive nominal phrase only; a syntactic phrase head is not automatically a semantic actor.")
    rows = [
        ("constituent_start_id", "string", "Token anchor at which the current constituent begins.", "t1", "the red rabbit", "rabbit ran", "completed determiner phrase", "return the start token anchor of the selected NP", "The selected NP is complete and its start is inside the visible context."),
        ("constituent_end_id", "string", "Visible token anchor closing the selected constituent.", "t3", "the red rabbit", "the very", "closed noun phrase", "return its last licensed token anchor", "Do not invent an end for a still-open phrase."),
        ("constituent_parent_id", "string", "Parse-node identifier of the immediate syntactic parent of the selected unit.", "np1", "the red rabbit", "red", "adjective attached inside a noun phrase", "return the parent NP node ID for the adjective attachment", "The parent is licensed in the prefix parse rather than supplied by a future token."),
        ("constituent_depth", "number", "Nesting depth of the selected constituent in its current parse candidate.", 2, "Lily saw the rabbit", "rabbit", "object NP nested under a verb phrase", "count parent edges to the clause root", "Count structural nesting, not the number of preceding words."),
        ("constituent_status", "string", "Completion state of the current constituent: open, complete, interrupted, or repaired.", "open", "Lily gave the", "Lily smiled .", "unfinished determiner phrase", "mark the NP as open until its head is supplied", "The determiner still requires an overt or licensed elided head."),
        ("expected_category", "string", "Syntactic category expected at the current prefix boundary.", "CN", "Lily held the", "Lily smiled .", "determiner awaiting nominal content", "retrieve the next unfilled category in the active NP production", "Keep multiple next categories when a phrase admits alternatives."),
        ("left_attachment_site_id", "string", "Previously visible phrase node that a new modifier may attach to.", "np1", "the rabbit beside", "beside", "postnominal prepositional modifier opener", "return the compatible visible NP attachment node", "A preceding NP exists and the attachment remains a candidate until disambiguated."),
        ("right_attachment_expectation", "string", "Type of following constituent still required by a modifier already read.", "adjective_phrase", "a very", "a rabbit", "degree modifier awaiting an adjective", "set the modifier's required host category", "The modifier is not used independently as a discourse interjection."),
        ("phrase_modifier_head_id", "string", "Token anchor of a modifier attached to the selected phrase.", "t2", "the red rabbit", "the rabbit", "attributively modified noun phrase", "retrieve the modifier head token from the NP analysis", "The modifier attachment is present; unmodified phrases abstain."),
        ("phrase_modifier_kind", "string", "Syntactic form of a phrase modifier, independent of its semantic relation.", "prepositional_phrase", "the rabbit by the tree", "the rabbit", "NP with postnominal prepositional phrase", "classify the attached modifier by its constituent category", "Do not infer location merely because a preposition is present."),
        ("phrase_complement_head_id", "string", "Head-token anchor of a syntactically selected phrase complement.", "t3", "proud of Lily", "proud", "adjective with selected of-complement", "retrieve the complement NP head anchor", "The prepositional phrase is selected by the adjective rather than a free adjunct."),
        ("phrase_specifier_head_id", "string", "Head-token anchor of a phrase's determiner or other specifier.", "t1", "the rabbit", "rabbits", "determined noun phrase", "return the determiner token anchor", "Bare nominals have no overt specifier to copy."),
        ("phrase_coordinator_id", "string", "Token anchor of the overt coordinator linking the selected conjunct.", "t2", "Lily and Ben", "Lily met Ben", "coordinated noun phrase", "return the conjunction token joining the current conjunct", "Distinguish coordination from an ordinary two-argument clause."),
        ("phrase_has_elision", "boolean", "Whether a recoverable syntactic head is omitted in the current phrase.", True, "the red one and the blue", "the blue bird", "nominal ellipsis licensed by a preceding parallel NP", "mark the omitted noun head as elided", "Require a recoverable nominal antecedent and a grammatical ellipsis construction."),
        ("phrase_discontinuity", "object", "Observed split-yield relation with host and displaced component anchors.", {"host": "np1", "displaced": "pp1"}, "Which box did Lily put the toy in", "Lily put the toy in the box", "extracted prepositional complement", "record the preposition and its displaced complement as one discontinuous dependency", "Do not infer discontinuity from arbitrary distance alone."),
        ("phrase_fronted", "boolean", "Whether the selected phrase occupies a licensed noncanonical left position.", True, "That book , Lily read", "Lily read that book", "object topicalization", "mark the preposed object phrase as fronted", "A compatible object gap is licensed by the prefix analysis."),
        ("phrase_extraposed", "boolean", "Whether a phrase is realized to the right of its canonical syntactic host.", True, "A story arrived that Lily loved", "A story that Lily loved arrived", "extraposed relative clause", "mark the right-displaced relative as extraposed from the subject NP", "Keep attachment ambiguity when the intervening predicate also licenses a complement."),
        ("phrase_apposition_id", "string", "Node identifier of an appositive paired with the current nominal.", "np2", "Lily , a painter", "Lily saw a painter", "nominal apposition", "link the second NP to the appositive relation node", "Punctuation alone does not license an identity claim."),
        ("phrase_repair_source_id", "string", "Anchor of the overt phrase being corrected by a visible repair.", "np1", "the red , no , the blue box", "the red and the blue box", "explicit nominal self-correction", "link the replacement NP to the corrected phrase", "A repair cue distinguishes correction from coordination."),
        ("phrase_selection_status", "string", "Whether an observed phrase satisfies its governor's category requirement.", "compatible", "Lily depended on Ben", "Lily depended that Ben", "selected on-prepositional complement", "compare the phrase category and marker with the governor's valency slot", "Use an explicit lexical frame and preserve alternative senses."),
        ("phrase_boundary_kind", "string", "Syntactic interpretation of a boundary at the current token.", "parenthetical_close", "Lily , the painter ,", "Lily and the painter", "closing parenthetical delimiter", "classify the current delimiter as a parenthetical close", "A matching visible opening delimiter exists in the same analysis."),
        ("phrase_separator_id", "string", "Anchor of punctuation separating the current phrase from a sibling phrase.", "t2", "Lily , Ben", "Lily met Ben", "comma-separated list prefix", "return the separator anchor between the visible list items", "Treat an incomplete list as a list hypothesis, not a complete sentence."),
        ("phrase_content_head_ids", "array", "Ordered head-token anchors of the content-bearing members of a phrase.", ["t1", "t3"], "Lily and Ben", "and", "coordinated nominal phrase", "collect each completed conjunct's head token anchor", "Exclude coordinators and punctuation from content heads."),
        ("phrase_attachment_candidates", "array", "Alternative syntactic attachment nodes still compatible with the prefix.", ["vp1", "np1"], "Lily saw Ben with binoculars", "Lily slept", "ambiguous prepositional attachment", "retain both NP and VP attachment nodes until evidence distinguishes them", "Do not resolve an instrument versus possession reading by recency alone."),
        ("phrase_embedding_path", "array", "Ordered syntactic node path locating the current constituent within enclosing phrases.", ["cl1", "vp1", "np1"], "Lily saw the rabbit", "rabbit", "object NP inside a finite clause", "return the active ancestor-node path", "Use parse-node identity rather than copying word strings."),
        ("constituent_category_alternatives", "array", "Unresolved category interpretations for a completed visible token span.", ["NP", "VP"], "visiting relatives", "the rabbit", "locally ambiguous gerund-participial span", "retain nominal and verbal span analyses", "Do not collapse the alternatives before a discriminating continuation is visible."),
        ("phrase_yield_shape", "string", "Observed ordering pattern of the selected phrase's constituents.", "determiner_adjective_noun", "the red rabbit", "rabbit", "determiner–modifier–head noun phrase", "summarize constituent roles in their observed order", "Summarize structure, not a memorized lexical phrase."),
        ("phrase_attachment_status", "string", "Whether a phrase's syntactic parent is resolved, ambiguous, or pending.", "ambiguous", "Lily saw Ben with binoculars", "Lily slept", "unresolved PP attachment", "mark the attachment unresolved while retaining licensed parents", "Require at least two compatible parse attachments."),
        ("phrase_obligation_ids", "array", "Identifiers of still-open syntactic requirements owned by the current phrase.", ["slot_object_1"], "Lily put", "Lily slept", "locative verb phrase awaiting complements", "collect unsatisfied valency-slot identifiers for the selected verb sense", "Do not mark optional adjuncts as obligatory."),
        ("sentence_fragment_type", "string", "Licensed fragment construction at a visible utterance boundary.", "nominal_answer", "Who arrived ? Lily .", "Lily arrived .", "nominal short answer", "classify the NP-only utterance as an answer fragment", "The preceding question licenses the missing clause structure."),
    ]
    for key, typ, desc, value, pos, neg, construction, compute, guard in rows:
        contract(key, typ, desc, f, value, pos, neg, construction, compute, guard=guard)
    assert len(c.attributes) == 32

    # 2. Grammatical relation links are independent of semantic event roles.
    f = "grammatical_relations"
    native("grammatical_subject_id", "entity_ref", "Entity denoted by an overt grammatical subject; this is not necessarily an actor.", f,
           "e1", seq(tok("subject", token="Lily", pos="n", entity_id=present()), tok(token="smiled", pos="v")),
           [{"token": "Lily", "pos": "n", "entity_id": "e1"}, {"token": "smiled", "pos": "v"}],
           [{"token": "Lily", "pos": "n", "entity_id": "e1"}, {"token": "nearby", "pos": "adv"}],
           emit={"grammatical_subject_id": ref("subject.entity_id")}, scope="finite predicate")
    relation_rows = [
        ("grammatical_object_id", "entity_ref", "Entity denoted by a direct object in the selected construction.", "e2", "Lily carried a box", "A box fell", "overt direct object", "retrieve the object NP's grounded entity identifier", "The verb licenses a direct object in this sense."),
        ("indirect_object_id", "entity_ref", "Entity denoted by the indirect object of a double-object construction.", "e2", "Lily gave Ben a box", "Lily saw Ben", "double-object dative", "retrieve the first object NP's grounded entity identifier", "The lexical frame licenses two objects; an ordinary direct object is not indirect."),
        ("oblique_complement_id", "string", "Phrase-node identifier of a selected oblique complement.", "pp1", "Lily relied on Ben", "Lily rested near Ben", "selected prepositional complement", "return the selected PP node", "Separate a verb-selected complement from a free locative adjunct."),
        ("predicative_complement_id", "string", "Head anchor of a complement predicated of a subject or object.", "ap1", "Lily became quiet", "Lily spoke quietly", "subject-oriented predicative complement", "retrieve the adjective phrase predicate node", "The phrase is a selected predicate, not a manner adverb."),
        ("copular_link_id", "string", "Anchor of the copular verb relating a subject to a nonverbal predicate.", "t2", "Lily is quiet", "Lily is running", "adjectival copular clause", "return the copula token anchor", "Distinguish copular be from progressive auxiliary be."),
        ("agentive_by_phrase_id", "string", "Node of an overt by-phrase licensed as a passive agent phrase.", "pp1", "The box was opened by Lily", "The box stood by Lily", "passive agent by-phrase", "retrieve the passive clause's agentive PP node", "An established passive construction distinguishes agency from spatial by."),
        ("prepositional_object_id", "entity_ref", "Entity denoted by the NP complement of a preposition.", "e2", "Lily sat beside Ben", "Lily sat beside", "completed prepositional phrase", "retrieve the complement NP's entity identifier", "The NP must be visible and entity-denoting."),
        ("genitive_dependent_id", "string", "Node identifier of a genitive dependent attached to a nominal head.", "np1", "Lily's book", "Lily read a book", "prenominal genitive", "return the genitive dependent node", "Genitive syntax alone does not prove ownership."),
        ("possessive_determiner_id", "string", "Token anchor of an overt possessive determiner.", "t1", "her book", "the book", "possessive determiner phrase", "return the possessive determiner token anchor", "Distinguish possessive determiner her from object pronoun her."),
        ("appositive_dependent_id", "string", "Node of a dependent nominal in an apposition construction.", "np2", "Lily , a painter", "Lily hired a painter", "supplementary nominal apposition", "return the appended nominal node", "The two NPs are in apposition, not separate verb arguments."),
        ("vocative_id", "string", "Token or phrase anchor of an overt addressee expression used vocatively.", "np1", "Lily , come here", "Lily came here", "imperative with vocative", "identify the detached address NP", "A subject mention without address syntax is not a vocative."),
        ("expletive_subject_id", "string", "Anchor of a syntactic subject without an ordinary referential entity.", "t1", "There is a rabbit", "There the rabbit sat", "existential there subject", "return the expletive there token anchor", "Separate existential there from locative there."),
        ("clausal_subject_id", "string", "Node identifier of a clause functioning as the subject.", "cl2", "That Lily won surprised Ben", "Lily said that Ben won", "finite clausal subject", "return the embedded clause in the subject position", "The clause is an argument of the matrix predicate in subject position."),
        ("clausal_object_id", "string", "Node identifier of a clause selected as a verb's content complement.", "cl2", "Lily knew that Ben won", "Lily rested because Ben won", "selected finite content clause", "return the complement clause node", "A causal adjunct is not a content complement."),
        ("adjunct_head_id", "string", "Head anchor of an optional syntactic modifier of the current predicate.", "adv1", "Lily slept peacefully", "Lily depended on Ben", "manner adjunct", "return the optional adverbial modifier head", "Use the predicate's frame to distinguish adjunct from selected complement."),
        ("adnominal_clause_id", "string", "Node of a clause attached to a nominal as a modifier.", "rel1", "the rabbit that hopped", "Lily knew that it hopped", "relative clause modifying a noun", "return the noun-attached clause node", "The same complementizer word may introduce a selected content clause elsewhere."),
        ("sentential_adverb_id", "string", "Anchor of an adverbial modifying a clause-level proposition.", "t1", "Fortunately , Lily arrived", "Lily arrived quietly", "sentence-oriented adverbial", "retrieve the clause-level modifier anchor", "Distinguish proposition-level evaluation from event manner."),
        ("particle_head_id", "string", "Anchor of the particle in a phrasal-verb construction.", "t3", "Lily picked up the box", "Lily walked up the hill", "verb-particle construction", "return the particle linked to the lexical verb", "Distinguish a selected particle from a path preposition."),
        ("auxiliary_head_id", "string", "Anchor of an auxiliary attached to the current lexical predicate.", "t2", "Lily has left", "Lily has a book", "perfect auxiliary construction", "retrieve the auxiliary token governing the participle", "Possessive have is a lexical verb rather than an auxiliary."),
        ("marker_head_id", "string", "Anchor of a subordinator or complementizer introducing the current clause.", "t3", "Lily knew that Ben left", "Lily knew Ben", "marked embedded clause", "return the clause introducer anchor", "Require a clausal attachment, not a homographic determiner."),
        ("relative_gap_governor_id", "string", "Predicate anchor whose argument position is associated with a relative gap.", "t4", "the book Lily read", "Lily read the book", "zero object relative", "link the relative gap to its governing verb", "Keep the head noun and relative predicate in the same relative construction."),
        ("subject_controller_id", "entity_ref", "Entity controlling the understood subject of a subject-control infinitive.", "e1", "Lily promised to leave", "Lily persuaded Ben to leave", "subject-control infinitive", "copy the matrix subject's entity ID to the understood infinitival subject", "Require a subject-control lexical sense, not arbitrary NP proximity."),
        ("object_controller_id", "entity_ref", "Entity controlling the understood subject of an object-control infinitive.", "e2", "Lily persuaded Ben to leave", "Lily promised Ben to leave", "object-control infinitive", "copy the matrix object's entity ID to the understood infinitival subject", "Require an object-control lexical sense."),
        ("raising_source_id", "string", "Clause node from which a raised syntactic subject receives its lower relation.", "cl2", "Lily seemed to sleep", "Lily tried to sleep", "subject raising", "link the raised subject to the infinitival subject position", "Distinguish raising from intentional subject control."),
        ("shared_subject_id", "entity_ref", "Entity denoted by an overt subject shared across coordinated predicates.", "e1", "Lily sang and danced", "Lily sang and Ben danced", "VP coordination with one subject", "copy the first predicate's grammatical subject ID to the later conjunct", "A new overt subject blocks subject sharing."),
        ("shared_object_id", "entity_ref", "Entity denoted by a visibly shared object of coordinated predicates.", "e2", "Lily bought and read the book", "Lily bought apples and read a book", "coordinated predicates sharing a rightmost object", "associate the object NP with both compatible verb frames", "Both predicates license the same object category."),
        ("syntactic_governor_id", "string", "Token anchor of the current token's immediate syntactic governor.", "t2", "Lily smiled warmly", "warmly", "verb-attached manner modifier", "return the governing lexical verb anchor", "A governor must be recoverable in the visible parse."),
        ("dependency_relation", "string", "Syntactic relation label between the current unit and its governor.", "adjectival_modifier", "a red rabbit", "the rabbit ran", "attributive adjective dependency", "label the adjective-to-noun edge", "Do not equate dependency label with a semantic event role."),
        ("dependency_distance", "number", "Visible token distance along a selected dependency edge.", 2, "Lily quickly smiled", "Lily", "overt subject linked across an adverb", "subtract the linked token positions and take absolute distance", "A resolved dependency edge is required before computing distance."),
        ("dependency_direction", "string", "Whether a selected dependent lies before or after its governor.", "dependent_before_governor", "red rabbit", "rabbit", "prenominal adjective dependency", "compare the visible anchors of dependent and governor", "The dependent and governor must belong to the same selected analysis."),
        ("dependency_status", "string", "Resolution state of the current dependency: pending, resolved, or ambiguous.", "pending", "Lily put the box on", "Lily slept .", "preposition awaiting its object", "mark the missing complement edge as pending", "A required complement remains unfilled at the current prefix boundary."),
    ]
    for key, typ, desc, value, pos, neg, construction, compute, guard in relation_rows:
        contract(key, typ, desc, f, value, pos, neg, construction, compute, guard=guard,
                 requires=("incremental_dependency_analysis", "typed_anchor_resolution"))
    assert len(c.attributes) == 64

    # 3. Valency is about licensed slots and expectations, not future fillers.
    f = "valency_expectations"
    valency_lex = [
        ("verb_valency_frame", "string", "Lexical verb's candidate argument-category frame.", {"slept": "subject_only", "admired": "subject_object", "gave": "subject_indirect_direct"}, "v", ("sleep", "n")),
        ("nominal_valency_frame", "string", "Candidate complement frame of a relational noun.", {"sister": "related_entity", "distance": "two_endpoints", "belief": "content"}, "n", "stone"),
        ("adjective_valency_frame", "string", "Candidate selected-complement frame of an adjective.", {"afraid": "of_or_content", "eager": "to_infinitive", "similar": "to_np"}, "adj", "wooden"),
        ("preposition_valency_frame", "string", "Candidate syntactic complement frame of a preposition.", {"between": "plural_np_or_coordination", "despite": "np_or_gerund", "during": "np"}, "prep", ("and", "conj")),
        ("expected_complement_preposition", "string", "Lexically selected preposition expected by a pending complement slot.", {"relied": "on", "consisted": "of", "belonged": "to"}, "v", "slept"),
        ("selected_complement_case", "string", "Case requirement on a lexical item's pronominal complement.", {"with": "objective", "beside": "objective", "for": "objective"}, "prep", ("for", "conj")),
        ("complement_control_type", "string", "Candidate source of an infinitival complement's understood subject.", {"persuaded": "object_control", "tried": "subject_control", "seemed": "raising"}, "v", "slept"),
    ]
    for key, typ, desc, mapping, pos, contrast in valency_lex:
        lex(key, typ, desc, f, mapping, pos, contrast,
            notes="Lexical evidence supplies a frame hypothesis; it does not assert a later complement or event participant.")
    pair("particle_separability", "string", "Lexical permission for a particle to separate from its verb around an object.", f,
         "picked", "up", "separable", "flowers",
         notes="The whole pick-up lexical construction supplies this permission; the word up alone is insufficient.")
    valency_rows = [
        ("expected_direct_object", "string", "Category requirement for a still-open direct-object slot.", "NP", "Lily admired", "Lily slept", "unsaturated transitive verb frame", "emit the direct-object slot's NP category", "The current verb sense licenses an object and none has yet filled its slot."),
        ("expected_indirect_object", "string", "Category requirement for an indirect-object slot in a selected double-object frame.", "NP", "Lily gave", "Lily admired", "candidate double-object dative frame", "emit the selected frame's first object category", "Preserve a prepositional-dative alternative rather than forcing one realization."),
        ("expected_predicative", "string", "Category required for a pending subject- or object-predicative complement.", "AP_or_NP", "Lily became", "Lily slept", "unsaturated change-of-state copular frame", "emit the selected frame's nonverbal predicate category", "This is an expectation, not an assertion that the change succeeded."),
        ("expected_clausal_complement", "string", "Type of finite clause accepted by a pending content slot.", "declarative", "Lily believed", "Lily slept", "verb selecting a finite content clause", "emit the compatible embedded-clause type", "Retain alternative lexical frames when the prefix does not select one."),
        ("expected_infinitive_complement", "boolean", "Whether the chosen frame currently requires or allows a to-infinitive complement.", True, "Lily intended", "Lily slept", "intent predicate with open infinitival slot", "activate the to-infinitive expectation", "Do not infer that the intended action happened."),
        ("expected_gerund_complement", "boolean", "Whether an unsaturated frame licenses a gerund-participial complement.", True, "Lily enjoyed", "Lily arrived", "verb selecting a gerund-participial clause", "activate the gerund-complement expectation", "Other possible object frames remain separate candidates."),
        ("expected_bare_infinitive", "boolean", "Whether a selected auxiliary or complement frame requires an unmarked verb form.", True, "Lily can", "Lily has", "modal auxiliary awaiting a bare infinitive", "set the unmarked-verb expectation", "Distinguish modal auxiliary can from a lexical noun or verb."),
        ("expected_pp_complement", "boolean", "Whether a selected frame contains an open prepositional complement slot.", True, "Lily depended", "Lily slept", "verb with selected PP complement", "activate the required PP-slot expectation", "A freely attachable PP adjunct is insufficient."),
        ("complement_slot_count", "number", "Number of syntactically selected complement slots in the active lexical frame.", 2, "Lily put", "Lily slept", "placement verb frame", "count the direct-object and location-complement slots", "Count selected slots rather than observed word frequency."),
        ("satisfied_complement_slots", "array", "Slot identifiers already filled in the current valency frame.", ["direct_object"], "Lily put the box", "Lily put", "partly saturated placement frame", "collect completed slot bindings from the selected analysis", "Do not count the still-missing location complement as filled."),
        ("open_complement_slots", "array", "Slot identifiers remaining unfilled in the current valency frame.", ["location_complement"], "Lily put the box", "Lily placed the box on a shelf", "placement predicate with missing location", "subtract visibly filled slots from required frame slots", "Slot identity and selected frame must be known."),
        ("optional_complement_slots", "array", "Selected argument slots that the active lexical sense allows to be omitted.", ["recipient"], "Lily donated a book", "Lily put a book", "donation frame with optional recipient", "retrieve omission permissions from the lexical frame", "Optional arguments differ from arbitrary adjuncts."),
        ("omitted_complement_reason", "string", "Constructional license for a missing complement at a completed boundary.", "understood_generic_object", "Lily ate .", "Lily put .", "licensed null object", "record the lexical null-complement license", "Do not treat every incomplete transitive clause as licensed omission."),
        ("selected_complement_mood", "string", "Mood required or preferred by a visible complement-selecting construction.", "mandative_subjunctive", "Lily insisted that Ben be", "Lily knew that Ben was", "mandative that-clause", "identify the selected bare-form subjunctive pattern", "The mandative reading must be supported; ordinary assertion is another sense."),
        ("selected_complement_finiteness", "string", "Finiteness constraint on a selected complement clause.", "nonfinite", "Lily tried to leave", "Lily knew that Ben left", "to-infinitival complement", "record the complement's required nonfinite form", "Do not copy matrix-clause tense into the infinitive."),
        ("selected_complement_subject", "string", "Constructional requirement for an overt or controlled embedded subject.", "overt_accusative", "Lily expected him to leave", "Lily tried to leave", "exceptional-case-marking infinitive", "record the overt embedded-subject requirement", "The pronoun is the lower subject in this selected analysis."),
        ("copular_complement_type", "string", "Syntactic type of a visibly selected copular complement.", "adjective_phrase", "Lily is very quiet", "Lily is running", "copular adjective predicate", "classify the nonverbal predicate category", "Auxiliary be must be excluded."),
        ("argument_alternation", "string", "Observed syntactic realization variant of one lexical frame.", "prepositional_dative", "Lily gave a book to Ben", "Lily slept near Ben", "prepositional dative", "identify the NP plus to-PP realization of a transfer frame", "A to-PP alone does not establish a dative alternation."),
        ("valency_saturation", "string", "Whether every obligatory complement slot has a visible or licensed filler.", "saturated", "Lily put the box on the shelf", "Lily put the box", "completed placement frame", "check required slots for overt or licensed completion", "Optional modifiers do not affect saturation."),
        ("expletive_license", "boolean", "Whether the selected construction licenses a nonreferential syntactic subject.", True, "It seems that Lily left", "Lily seems tired", "extraposed clausal subject with dummy it", "license the dummy-subject analysis", "Do not erase a referential it reading without constructional evidence."),
        ("extraction_license", "string", "Kind of argument gap licensed by the visible extraction construction.", "object_gap", "Which book did Lily read", "Lily read the book", "wh-object extraction", "record the object position as licensed to remain unexpressed locally", "Require a matching filler and compatible governor."),
        ("passive_license", "boolean", "Whether a chosen lexical argument frame admits a passive realization.", True, "the book was read", "Lily resembled Ben", "passive-compatible transitive frame", "consult the verb sense's passivization constraint", "Do not equate all transitive-looking frames with passive eligibility."),
        ("object_predicate_requirement", "string", "Predicative complement type selected in an object-complement construction.", "AP", "Lily considered Ben", "Lily admired Ben", "object-oriented predicative frame", "keep the selected predicative slot open after the object", "Retain other lexical senses of consider as separate possibilities."),
        ("preposition_stranding_license", "boolean", "Whether a selected gap construction permits the preposition to remain behind its complement.", True, "Which chair did Lily sit on", "Lily sat on the chair", "stranded preposition in a wh-question", "link the final preposition to the earlier extracted complement", "Require a completed filler–gap dependency rather than a truncated PP."),
    ]
    for key, typ, desc, value, pos, neg, construction, compute, guard in valency_rows:
        contract(key, typ, desc, f, value, pos, neg, construction, compute, guard=guard,
                 requires=("lexical_valency_lexicon", "incremental_slot_tracking"))
    assert len(c.attributes) == 96

    # 4. Inflection: attested forms supply bounded, type-safe lexical seeds.
    f = "inflection_agreement"
    morphology = [
        ("grammatical_number", "string", "Morphosyntactic number of the current nominal form.", {"rabbits": "plural", "children": "plural", "rabbit": "singular"}, "n", "scenery"),
        ("grammatical_person", "number", "Grammatical person expressed by a personal pronoun.", {"I": 1, "we": 1, "you": 2, "they": 3}, "pron", "who"),
        ("grammatical_gender", "string", "Gender specification of a grammatical form, without inferring a person's gender from a name.", {"she": "feminine", "he": "masculine", "it": "neuter"}, "pron", "they"),
        ("grammatical_case", "string", "Case expressed by an overt pronoun form.", {"him": "objective", "he": "nominative", "her": "objective"}, "pron", "you"),
        ("grammatical_animacy", "string", "Grammatical human/nonhuman selection associated with an interrogative or relative form.", {"who": "human", "whom": "human", "which": "unrestricted"}, "pron", "it"),
        ("adjective_degree", "string", "Morphologically expressed comparison degree of an adjective.", {"smaller": "comparative", "smallest": "superlative", "small": "positive"}, "adj", "wooden"),
        ("adverb_degree", "string", "Morphologically expressed comparison degree of an adverb.", {"faster": "comparative", "fastest": "superlative", "fast": "positive"}, "adv", "yesterday"),
        ("verb_form", "string", "Inflectional form class of a verbal token, leaving ambiguous forms unresolved.", {"running": "gerund_participle", "eaten": "past_participle", "walks": "finite_third_singular"}, "v", "cut"),
        ("noun_countability", "string", "Lexical countability candidate of a noun in its ordinary reading.", {"furniture": "mass", "rabbit": "count", "water": "mass"}, "n", "chicken"),
        ("inflection_class", "string", "Lexical inflection paradigm class relevant to selecting a surface form.", {"children": "child_irregular_plural", "mice": "mouse_irregular_plural", "feet": "foot_irregular_plural"}, "n", "stone"),
        ("inflection_is_irregular", "boolean", "Whether the observed form belongs to a listed irregular paradigm.", {"went": True, "saw": True, "ate": True}, "v", "walked"),
        ("inflection_alternation", "string", "Morphological alternation producing a recognized inflected nominal form.", {"mice": "internal_vowel_change", "children": "irregular_suffixation", "rabbits": "regular_suffixation"}, "n", "news"),
        ("inflection_suffix", "string", "Recognized inflectional suffix of the current word form.", {"walked": "ed", "walking": "ing", "walks": "s"}, "v", "sing"),
        ("inflection_prefix", "string", "Recognized bound inflectional prefix in an explicitly marked archaic English form.", {"yclept": "y"}, "v", "yelled"),
        ("derivational_base", "string", "Base lexeme of an overt derived word, distinct from ordinary inflectional lemmatization.", {"kindness": "kind", "happiness": "happy", "movement": "move"}, "n", "business"),
        ("derivational_process", "string", "Morphological derivation evidenced by the current lexical form.", {"kindness": "adjective_to_abstract_noun", "runner": "verb_to_agent_noun"}, "n", "corner"),
        ("contraction_expansion", "array", "Lexical expansion of an unambiguous written contraction.", {"can't": ["can", "not"], "won't": ["will", "not"], "don't": ["do", "not"]}, "v", "he's"),
        ("clitic_type", "string", "Grammatical class of an overt clitic token supplied by tokenization.", {"n't": "negative", "'ll": "modal_auxiliary", "'ve": "perfect_auxiliary"}, "clitic", "'s"),
        ("genitive_realization", "string", "Overt form used for a genitive-dependent construction.", {"Lily's": "singular_s_clitic", "children's": "plural_s_clitic"}, "n", ("hers", "pron")),
        ("plural_allomorph", "string", "Written morphological realization of a recognized noun plural.", {"boxes": "es_suffix", "rabbits": "s_suffix", "children": "ren_irregular"}, "n", "sheep"),
        ("participial_allomorph", "string", "Recognized written realization of a past participle.", {"eaten": "en_suffix", "walked": "ed_suffix", "gone": "suppletive_or_irregular"}, "v", "cut"),
        ("reflexive_form", "string", "Morphological reflexive-series form of the current pronoun; singular-they-compatible forms retain number uncertainty.", {"herself": "third_singular_feminine", "themselves": "third_person_number_underspecified", "myself": "first_singular"}, "pron", "her"),
        ("personal_pronoun_series", "string", "Inflectional series to which an overt personal-pronoun form belongs.", {"mine": "independent_possessive", "hers": "independent_possessive", "me": "objective"}, "pron", "who"),
        ("adjective_inflection_pattern", "string", "Lexical comparison paradigm associated with the adjective.", {"better": "good_suppletive", "worse": "bad_suppletive", "smaller": "regular_er_est"}, "adj", "unique"),
        ("suppletion_type", "string", "Kind of nonconcatenative stem replacement in an overt suppletive paradigm.", {"went": "full_stem_replacement", "was": "full_stem_replacement", "were": "full_stem_replacement"}, "v", "walked"),
    ]
    for key, typ, desc, mapping, pos, contrast in morphology:
        lex(key, typ, desc, f, mapping, pos, contrast,
            notes="Finite lookup seed, not a suffix heuristic or a general morphological analyzer; ambiguous/coerced uses may abstain.")
    agreement_rows = [
        ("agreement_controller_id", "string", "Syntactic node identifier of the constituent whose features control an agreement relation.", "np1", "The rabbits are", "The rabbits", "subject–finite-verb agreement", "retrieve the subject NP node identifier as controller", "A finite agreement target is visible."),
        ("agreement_domain_id", "string", "Syntactic domain identifier within which the selected agreement relation applies.", "cl1", "The rabbits are", "Rabbits", "finite subject agreement domain", "return the clause node containing both controller and target", "Do not join controller and target across an intervening clause boundary."),
        ("agreement_requirements", "object", "Typed bundle of feature values required on an agreement target.", {"number": "plural", "person": 3}, "The rabbits are", "The rabbit is", "plural subject agreement", "project the subject's grammatical number and person as target constraints", "Constraints are a joint requirement bundle, not inferred lexical semantics."),
        ("agreement_satisfied", "boolean", "Whether a selected overt agreement pair has compatible known feature values.", True, "The rabbits are", "The rabbits is", "compatible subject–verb agreement", "unify known controller and target agreement features", "Unknown agreement values must not count as proven compatibility."),
        ("agreement_conflict", "object", "Observed conflicting values in a selected agreement relation.", {"feature": "number", "controller": "plural", "target": "singular"}, "The rabbits is", "The rabbits are", "subject–verb number mismatch", "return the incompatible known agreement values", "Preserve the raw observed form; flag conflict without silently correcting it."),
        ("case_assignment_source_id", "string", "Anchor of the governor that licenses the current constituent's case.", "t1", "with him", "he", "objective pronoun governed by a preposition", "return the governing preposition token anchor", "Do not assign case from semantic role alone."),
        ("case_syncretism", "array", "Case analyses that remain indistinguishable in the observed surface form.", ["nominative", "objective"], "you", "him", "case-syncretic personal pronoun", "retain the form's lexical case alternatives", "Later syntax may select one case, but the surface form itself does not."),
    ]
    for key, typ, desc, value, pos, neg, construction, compute, guard in agreement_rows:
        contract(key, typ, desc, f, value, pos, neg, construction, compute, guard=guard,
                 requires=("incremental_dependency_analysis", "feature_unification"))
    assert len(c.attributes) == 128

    # 5. Nominal constructions preserve interpretation uncertainty.
    f = "nominal_constructions"
    nominal_lex = [
        ("determiner_kind", "string", "Grammatical subclass of an overt determiner.", {"the": "definite_article", "a": "indefinite_article", "every": "universal_distributive"}, "det", ("and", "conj")),
        ("definiteness", "string", "Definiteness encoded by the selected nominal determiner.", {"the": "definite", "a": "indefinite", "an": "indefinite"}, "det", "some"),
    ]
    for key, typ, desc, mapping, pos, contrast in nominal_lex:
        lex(key, typ, desc, f, mapping, pos, contrast)
    pair("predeterminer_kind", "string", "Grammatical subclass of an overt modifier preceding an ordinary determiner.", f,
         "all", "the", "universal", "rabbits",
         notes="The observed determiner stack establishes predeterminer use; all without the following determiner does not.")
    nominal_pairs = [
        ("nominal_head_kind", "string", "Type of syntactic head in a nominal construction.", "the", "rich", "nominalized_adjective", "rabbit"),
        ("possessive_construction", "string", "Observed syntactic construction expressing a genitive relation.", "Lily's", "book", "prenominal_s_genitive", "quickly"),
        ("partitive_construction", "boolean", "Evidence for a partitive selecting members from an explicit nominal domain.", "some", "of", True, "rabbits"),
        ("pseudopartitive_construction", "boolean", "Evidence for a measure/container nominal followed by an of-complement.", "cup", "of", True, "fell"),
        ("bare_nominal_use", "string", "Constructional use of a noun without an overt determiner.", "at", "school", "institutional_bare_singular", "the"),
        ("postpositive_adjective", "boolean", "Evidence for an adjective following an indefinite-pronoun nominal head.", "something", "strange", True, "happened"),
        ("nominalization_kind", "string", "Overt construction converting a predicate into a nominal expression.", "the", "singing", "gerund_nominal_candidate", "rabbit"),
    ]
    for key, typ, desc, left, right, value, contrast in nominal_pairs:
        pair(key, typ, desc, f, left, right, value, contrast,
             notes="Construction evidence only; no ownership, quantity, existence, or successful action is asserted.")
    nominal_rows = [
        ("specificity", "string", "Whether visible grammar explicitly supports a particular versus nonspecific nominal reading.", "specific_marked", "a certain rabbit", "a rabbit", "certain-marked indefinite", "mark specificity as explicitly signaled", "Do not infer specificity for every indefinite noun phrase."),
        ("referential_use", "string", "Syntactic use of a nominal as referential, predicative, attributive, or expletive.", "predicative", "Lily became a teacher", "A teacher arrived", "predicate nominal", "classify the nominal's use in the copular construction", "Do not allocate a new individual solely for a predicate nominal."),
        ("proper_name_structure", "string", "Internal grammatical construction of an overt proper-name phrase.", "title_plus_name", "Doctor Lily", "a doctor", "title followed by proper name", "classify the title–name arrangement", "A title is a linguistic form, not proof of credentials."),
        ("nominal_modification_order", "array", "Observed ordered modifier classes before a nominal head.", ["size", "color"], "a small red box", "a box", "stacked prenominal modifiers", "record the visible adjective-class ordering", "Use lexical adjective classifications without enforcing universal ordering laws."),
        ("adjective_position", "string", "Syntactic position of an adjective relative to its nominal or clause host.", "attributive_prenominal", "a red box", "the box is red", "prenominal attributive adjective", "record the adjective's constructional position", "Distinguish attributive position from predicate complement position."),
        ("adjective_interpretation", "string", "Candidate semantic composition class of an adjective–noun combination.", "privative", "a fake diamond", "a red diamond", "privative nominal modification", "select the adjective sense's privative composition hypothesis", "Do not infer that the head noun's ordinary denotation holds under a privative modifier."),
        ("relational_noun_kind", "string", "Kind of argument relation lexically selected by a nominal head.", "kinship_relation", "the sister of Lily", "the picture of Lily", "kinship relational noun", "identify the noun sense's relational argument kind", "This classifies the expression; it does not verify the relation in the physical world."),
        ("nominal_complement_type", "string", "Category of a visibly selected complement of a noun.", "finite_content_clause", "the belief that Lily left", "the rabbit that Lily saw", "noun-selected content clause", "classify the selected clausal complement", "Distinguish a content clause from a relative modifier."),
        ("genitive_attachment", "string", "Nominal node to which a visible genitive construction attaches.", "np_book", "the girl's brother's book", "the girl read a book", "nested genitive attachment", "identify the nominal immediately licensed by the genitive phrase", "Retain structural nesting instead of flattening all possessors."),
        ("apposition_kind", "string", "Constructional subtype of an appositive nominal relation.", "supplementary", "Lily , a painter ,", "the painter Lily", "comma-delimited nominal apposition", "classify the apposition as supplementary", "Punctuation must align with a compatible nominal apposition parse."),
        ("measure_noun_role", "string", "Syntactic role of a measure noun in a nominal measure expression.", "measure_head", "three cups of water", "three cups broke", "measure nominal with material complement", "classify cup as the measure head of the NP", "This field contains syntax, not numerical amount or unit conversion."),
        ("classifier_type", "string", "Constructional subtype of a classifier-like noun in English measure/group phrases.", "group_classifier", "a flock of birds", "a bird near a flock", "collective classifier phrase", "classify the leading noun's grouping function", "Do not infer exact cardinality from the classifier."),
        ("distributive_nominal_form", "string", "Overt nominal form that supplies distributive syntax.", "each_determiner", "each rabbit", "the rabbits", "each-determined NP", "record the distributive determiner construction", "Distribution concerns the expression's interpretation, not an observed repeated event."),
        ("nominalization_argument_mapping", "object", "Candidate mapping from nominal dependents to the source predicate's argument slots.", {"of_complement": "theme", "by_complement": "agent"}, "the destruction of the tower by Lily", "the picture of Lily", "event nominal with of and by dependents", "map dependents using the nominalization's lexical argument frame", "Require an event-nominal sense; do not generalize to all of-phrases."),
        ("noun_compound_relation", "string", "Candidate semantic relation inside a noun–noun compound.", "material", "stone wall", "garden wall", "material-denoting noun compound", "retrieve a supported material relation for the compound sense", "Keep other compound senses separate; adjacency alone is insufficient."),
        ("noun_compound_head_id", "string", "Head-token anchor of a syntactically analyzed noun compound.", "t2", "garden wall", "garden grows", "right-headed English noun compound", "return the compound's nominal head anchor", "Require compound syntax rather than a subject–verb sequence."),
        ("nominal_clause_attachment", "string", "Attachment relation between a nominal and a following clause.", "relative_modifier", "the rabbit that hopped", "the claim that Lily won", "noun-modifying relative clause", "classify the clause as relative rather than noun-selected content", "The relative clause contains an appropriate gap or linked relative expression."),
        ("reduced_relative_kind", "string", "Nonfinite reduced-relative construction modifying a noun.", "passive_participial", "the box painted by Lily", "the box was painted", "past-participial reduced relative", "classify the reduced relative's passive form", "The participle modifies the noun rather than serving as the matrix predicate."),
        ("restrictive_modifier", "boolean", "Whether the selected nominal modifier has an integrated restrictive construction.", True, "the rabbits that hopped", "Lily , who smiled ,", "integrated relative modifier", "mark the relative as restricting the nominal domain", "Use the constructional analysis and preserve ambiguous punctuation-free cases."),
        ("determiner_stack_status", "string", "Compatibility state of multiple overt determiners within one nominal phrase.", "compatible_predeterminer_article", "all the rabbits", "the a rabbit", "predeterminer plus article", "check the determiners' ordered combinatorial classes", "Compatibility requires an actual determiner stack, not two adjacent separate NPs."),
        ("numeral_syntactic_role", "string", "Grammatical role of a numeral in its local phrase, distinct from its magnitude.", "nominal_determiner", "three rabbits", "rabbit number three", "cardinal modifying a noun", "classify the numeral as a cardinal determiner", "Do not compute quantity or identity in this syntactic field."),
        ("nominal_ellipsis_license", "string", "Constructional reason an omitted nominal head is recoverable.", "parallel_color_modifier", "the red box and the blue", "a blue", "parallel adjectival nominal ellipsis", "record the preceding nominal source that licenses noun omission", "A recoverable nominal antecedent and compatible modifier are required."),
    ]
    for key, typ, desc, value, pos, neg, construction, compute, guard in nominal_rows:
        contract(key, typ, desc, f, value, pos, neg, construction, compute, guard=guard)
    assert len(c.attributes) == 160

    # 6. Verbal syntax describes forms and candidate readings, not event truth.
    f = "verbal_constructions"
    verbal_lex = [
        ("tense", "string", "Morphosyntactic tense expressed by a finite verbal form.", {"went": "past", "sang": "past", "walks": "present"}, "v", "cut"),
        ("modal_auxiliary_class", "string", "Lexical class of a modal auxiliary without forcing one contextual modal sense.", {"must": "necessity_family", "may": "possibility_or_permission", "might": "possibility_family"}, "aux", "can"),
        ("negation_marker_form", "string", "Surface form of an overt grammatical negation marker at the current query.", {"not": "not", "never": "never", "n't": "n't"}, "adv", ("always", "adv")),
    ]
    for key, typ, desc, mapping, pos, contrast in verbal_lex:
        lex(key, typ, desc, f, mapping, pos, contrast,
            notes="This is grammatical evidence. It neither supplies an event timestamp nor establishes assertion/factuality.")
    subjunctive = "It is essential that she be"
    native("mood", "string", "Morphosyntactic mood evidenced by the current verbal construction, distinct from modal meaning.", f,
           "subjunctive", seq(gap(), *(tok(**row) for row in words(subjunctive))),
           words(subjunctive), words("It is clear that she is"),
           notes="Bare be after a third-person subject in this mandative construction supports subjunctive mood; may or must alone does not.")
    verbal_pairs = [
        ("aspect", "string", "Aspectual construction visibly realized by an auxiliary and lexical predicate.", "has", "eaten", "perfect", "apples"),
        ("voice", "string", "Voice realized by a visible auxiliary and participial construction.", "was", "arrested", "passive_candidate", "sleeping"),
        ("polarity", "string", "Overt grammatical negation of the current auxiliary construction.", "did", "not", "negative", "indeed"),
        ("auxiliary_selection", "string", "Form class selected by the observed auxiliary construction.", "has", "eaten", "past_participle", "apples"),
        ("participial_function", "string", "Syntactic function supported for the visible participle.", "is", "running", "progressive_lexical_predicate", "quiet"),
        ("gerund_function", "string", "Syntactic function supported for a gerund-participial form.", "enjoyed", "swimming", "selected_complement", "apples"),
        ("do_support_status", "string", "Evidence that do functions as a supporting auxiliary rather than a lexical verb.", "did", "not", "negative_support", "homework"),
        ("verb_particle_construction", "string", "Lexically supported verb–particle construction candidate.", "picked", "up", "pick_up", "flowers"),
        ("light_verb_construction", "string", "Candidate light-verb construction pairing a general verb with an event nominal.", "took", "care", "take_care", "scissors"),
        ("causative_syntax", "string", "Observed syntactic shape supporting a causative complement analysis.", "made", "him", "make_np_bare_infinitive_pending", "cakes"),
        ("perception_complement_syntax", "string", "Candidate category of a perception verb's visible complement, preserving nominal versus gerund-participial ambiguity.", "heard", "singing", "gerund_or_event_nominal_candidate", "music"),
        ("dative_alternation_form", "string", "Visible dative realization pattern at the selected prefix boundary.", "gave", "him", "double_object_candidate", "up"),
        ("subject_auxiliary_inversion", "boolean", "Evidence of a finite auxiliary before its overt pronominal subject.", "Did", "she", True, "indeed"),
        ("verb_phrase_ellipsis", "boolean", "Evidence of an auxiliary standing for an omitted parallel verb phrase.", "will", "too", True, "leave"),
        ("verb_phrase_anaphor", "string", "Overt proform used as a verbal predicate.", "did", "so", "do_so", "homework"),
    ]
    for key, typ, desc, left, right, value, contrast in verbal_pairs:
        if key == "causative_syntax":
            native(key, typ, desc, f, "make_np_bare_infinitive",
                   seq(gap(), tok(token="made"), tok(token="him"), tok(token="leave")),
                   words("made him leave"), words("made him cakes"))
            continue
        if key == "verb_phrase_ellipsis":
            phrase = "Lily will leave and Ben will too"
            native(key, typ, desc, f, True, seq(*(tok(**row) for row in words(phrase))),
                   words(phrase), words("Lily will leave and Ben will sing"),
                   notes="The complete seed includes a visible parallel antecedent; an isolated auxiliary is insufficient.")
            continue
        pair(key, typ, desc, f, left, right, value, contrast,
             notes="Finite construction seed; labels marked candidate remain hypotheses. No later object, outcome, or world-state commitment is supplied.")
    verbal_rows = [
        ("auxiliary_chain", "array", "Ordered auxiliary functions realized before the current lexical verb.", ["modal", "perfect", "progressive"], "Lily may have been running", "Lily ran", "stacked modal–perfect–progressive auxiliaries", "collect the auxiliary functions in grammatical scope order", "Do not collapse one auxiliary's ambiguity by borrowing a future predicate."),
        ("auxiliary_scope", "object", "Syntactic scope relation between a visible auxiliary and its complement predicate.", {"outer": "modal", "inner": "perfect"}, "Lily may have left", "Lily has a book", "modal taking a perfect VP complement", "record the outer-to-inner auxiliary relation", "Possessive have must not be mistaken for perfect have."),
        ("infinitive_marker_id", "string", "Token anchor of to when it introduces an infinitive.", "t3", "Lily tried to leave", "Lily went to school", "to-infinitive marker", "return the to token governing the bare verb", "Distinguish infinitival to from a preposition."),
        ("imperative_subject_status", "string", "Overt or constructionally understood subject status of an imperative.", "understood_addressee", "Please sit down", "Lily sat down", "subjectless polite imperative", "mark the syntactically understood addressee subject", "This supplies a grammatical role, not a resolved discourse addressee entity."),
        ("perfect_auxiliary_id", "string", "Anchor of the have auxiliary in a perfect construction.", "t2", "Lily has eaten", "Lily has apples", "perfect auxiliary plus participle", "return the have auxiliary anchor", "A past-participle complement establishes the auxiliary use."),
        ("progressive_auxiliary_id", "string", "Anchor of the be auxiliary in a progressive construction.", "t2", "Lily is running", "Lily is quiet", "progressive be plus participle", "return the be auxiliary anchor", "A verbal ing complement distinguishes progressive from copular be."),
        ("passive_auxiliary_id", "string", "Anchor of an auxiliary licensing a passive participial predicate.", "t3", "The box was opened by Lily", "The box was open", "eventive passive with agent phrase", "return the passive auxiliary anchor", "An adjective complement alone does not establish an eventive passive."),
        ("serial_verb_construction", "string", "Candidate serial or pseudo-serial construction containing adjacent lexical verbs.", "go_and_v_pseudocoordination", "Lily went and fetched water", "Lily went home and Ben fetched water", "same-subject go-and-verb pseudocoordination", "classify the linked verbs as a single constructional candidate", "Ordinary independent clause coordination must remain an alternative when licensed."),
        ("resultative_predicate_id", "string", "Node of an object-oriented predicate in a resultative construction.", "ap1", "Lily hammered the metal flat", "Lily hammered the flat metal", "object resultative predicate", "return the post-object result predicate node", "Constructional result meaning remains under the clause's modality and negation."),
        ("depictive_predicate_id", "string", "Node of a secondary predicate describing a participant during an event.", "ap1", "Lily ate the carrots raw", "Lily ate raw carrots", "object-oriented depictive predicate", "return the secondary predicate node and its syntactic attachment", "A prenominal adjective is not this secondary-predicate construction."),
        ("middle_construction", "boolean", "Whether a nonagentive-subject clause has a generic middle construction.", True, "This book reads easily", "Lily reads the book", "generic middle voice construction", "mark the surface middle construction", "The property reading must be supported; do not fabricate an implicit actor."),
        ("anticausative_construction", "boolean", "Whether an intransitive change predicate realizes the noncausative alternant of a transitive frame.", True, "The door opened", "Lily opened the door", "intransitive change-of-state alternant", "mark the noncausative syntactic realization", "Lexical alternation evidence is needed; surface intransitivity alone is insufficient."),
        ("locative_alternation_form", "string", "Observed syntactic arrangement of moved material and affected location.", "location_object_with_material", "Lily loaded the cart with hay", "Lily loaded hay onto the cart", "location-object locative alternation", "identify the object-as-location realization", "Retain semantic participant identity independently of grammatical object choice."),
    ]
    for key, typ, desc, value, pos, neg, construction, compute, guard in verbal_rows:
        contract(key, typ, desc, f, value, pos, neg, construction, compute, guard=guard)
    assert len(c.attributes) == 192

    # 7. Clause scope needs explicit state; lexical openers alone do not close it.
    f = "clause_scope"
    clause_lex = [
        ("complementizer_type", "string", "Lexical class of an explicitly annotated clause introducer.", {"that": "declarative", "whether": "interrogative", "if": "interrogative_or_conditional"}, "comp", ("the", "det")),
        ("subordinator_type", "string", "Lexical relation family signaled by an explicitly annotated subordinator.", {"because": "reason", "although": "concessive", "while": "temporal_or_contrast"}, "subord", "and"),
        ("clause_speech_form", "string", "Grammatical sentence-form evidence supplied by a final boundary mark.", {"?": "interrogative_punctuation", "!": "exclamative_punctuation"}, "punct", "."),
    ]
    for key, typ, desc, mapping, pos, contrast in clause_lex:
        lex(key, typ, desc, f, mapping, pos, contrast,
            notes="The marker supplies grammatical evidence only; it does not determine pragmatic speech act or the full clause's truth conditions.")
    clause_rows = [
        ("clause_id", "string", "Stable identifier for the current causal clause hypothesis.", "cl1", "Lily slept", "the rabbit", "finite subject–predicate clause", "allocate a clause anchor from its first visible clause-defining token", "Identity must be deterministic from visible anchors and remain stable across prefixes."),
        ("clause_type", "string", "Syntactic clause category in the current analysis.", "declarative", "Lily slept .", "Did Lily sleep ?", "closed declarative clause", "classify its observed finite-clause construction", "Use syntactic form rather than assuming every declarative is a sincere assertion."),
        ("clause_finiteness", "string", "Whether the selected clause has finite or nonfinite verbal syntax.", "nonfinite", "Lily tried to leave", "Lily left", "embedded to-infinitival clause", "classify the selected embedded clause as nonfinite", "Keep the matrix clause's finiteness separate."),
        ("clause_status", "string", "Incremental syntactic completion status of the selected clause.", "open", "Lily gave the", "Lily slept .", "clause with an unfinished argument phrase", "mark the clause as open while required structure remains incomplete", "An optional continuation must not by itself prevent syntactic completion."),
        ("matrix_clause_id", "string", "Identifier of the clause immediately embedding the selected clause.", "cl1", "Lily said that Ben left", "Ben left", "finite complement embedded under a reporting verb", "return the immediate parent-clause ID", "Do not confuse the reporting source with the embedded subject."),
        ("subordinate_clause_id", "string", "Identifier of a subordinate clause attached to the current matrix construction.", "cl2", "Lily smiled because Ben arrived", "Lily smiled", "causal subordinate clause", "return the attached subordinate-clause ID", "The subordinate node is present in the visible prefix analysis."),
        ("embedding_depth", "number", "Number of enclosing clause boundaries around the selected clause.", 1, "Lily said that Ben left", "Ben left", "one-level finite clausal embedding", "count clause-parent edges to the root clause", "Count clauses rather than all nominal and verbal phrase nodes."),
        ("complementizer_id", "string", "Token anchor of the complementizer introducing the selected embedded clause.", "t3", "Lily knew that Ben left", "Lily knew Ben", "that-marked content clause", "return the complementizer token anchor", "That must be a clause marker, not a determiner or demonstrative pronoun."),
        ("subordinator_id", "string", "Token anchor of the connective subordinating the selected clause.", "t3", "Lily left because Ben arrived", "Lily left and Ben arrived", "adverbial subordinate clause", "return the subordinating connective anchor", "Coordinators do not establish this relation."),
        ("clause_subject_requirement", "string", "Constructional requirement for the subject of the selected clause.", "controlled_or_understood", "Lily tried to leave", "Lily knew that Ben left", "subjectless to-infinitival complement", "record that the infinitival clause's subject is structurally understood", "Resolve controller identity separately from the requirement itself."),
        ("assertion_scope_id", "string", "Clause-level syntactic container for a candidate assertion, not proof that it is asserted.", "cl2", "Lily said that Ben left", "Lily said", "complete report content clause", "assign the embedded proposition its own assertion-container ID", "Do not promote reported content to narrator-endorsed fact."),
        ("negation_attachment_kind", "string", "Syntactic category and attachment level of an overt negator; semantic target identity is stored separately.", "VP", "Lily did not open the box", "Lily opened the box", "auxiliary-supported VP negation", "classify the negator's syntactic attachment as VP-level", "Keep narrower and wider readings as alternatives where syntax leaves them unresolved."),
        ("modal_scope_id", "string", "Node identifier for the predicate under a modal operator.", "vp1", "Lily might open the box", "Lily opened the box", "modal auxiliary governing a VP", "return the modal's complement VP scope", "A modalized event must not be silently promoted to actuality."),
        ("quotation_scope_id", "string", "Identifier of an open or closed syntactic quotation region.", "quote1", "Lily said , \" Hello", "Lily said hello", "overt open quotation", "allocate or retrieve the quote-region ID opened by the visible delimiter", "Do not require a future closing quote to establish an open region."),
        ("quantifier_scope_id", "string", "Syntactic scope node associated with a quantified nominal candidate.", "cl1", "Every rabbit slept", "The rabbit slept", "universal quantifier in subject position", "link the quantifier to its licensed clause-level scope candidate", "Do not force one scope ordering when multiple quantified phrases make it ambiguous."),
        ("scope_openers", "array", "Visible operator anchors opening syntactic interpretation scopes.", ["t1"], "If Lily leaves", "Lily leaves", "conditional antecedent scope opener", "append the if anchor to the current parse's open-scope stack", "Operators only open scopes licensed by their syntactic use."),
        ("scope_closers", "array", "Visible boundary anchors closing scopes under the selected construction.", ["t4"], "If Lily leaves ,", "If Lily leaves", "conditional antecedent boundary", "close the antecedent scope at its licensed comma boundary", "A comma only closes scopes established by the current parse, not arbitrary scopes."),
        ("scope_visibility_state", "object", "Syntactic accessibility constraints for referents introduced inside the current scope.", {"scope": "negated_clause", "exports_ordinary_referents": False}, "Lily did not buy a box .", "Lily bought a box .", "completed negated scope", "record that ordinary introduced referents remain inside their negated hypothesis", "This is an ACE-inspired constraint candidate; open English discourse can require richer accommodation."),
        ("scope_island_type", "string", "Construction type forming a syntactic extraction island candidate.", "relative_clause", "the rabbit that Lily saw", "Lily saw the rabbit", "relative-clause island", "label the subordinate relative as an extraction-island domain", "Record the domain; do not reject a sentence without an actual attempted extraction."),
        ("clause_attachment_site", "string", "Node identifier chosen as the syntactic host of the selected clause.", "np1", "the claim that Lily won", "Lily claimed that Ben won", "noun-selected content clause", "attach the content clause to the selecting nominal node", "The nearest word is insufficient without a compatible selecting construction."),
        ("clause_attachment_ambiguity", "array", "Alternative host nodes for a subordinate clause still compatible with the prefix.", ["vp1", "vp2"], "Lily said Ben left because it rained", "Because it rained , Ben left", "ambiguous low or high causal-clause attachment", "retain compatible matrix and embedded attachment nodes", "Do not silently assign the cause to the most recent event."),
        ("parenthetical_clause_status", "string", "Whether a visible clause is structurally supplementary to its host.", "supplementary", "Lily , I think , left", "I think Lily left", "medial parenthetical clause", "mark the inserted clause as parenthetical", "A normal matrix attitude predicate is not a parenthetical insertion."),
        ("small_clause_kind", "string", "Constructional type of a subject–predicate unit without a finite verb.", "np_ap", "Lily considered Ben clever", "Ben was clever", "object plus adjective small clause", "classify the selected NP–AP predicative unit", "Keep the matrix verb outside the small clause's subject–predicate pair."),
        ("verbless_clause_kind", "string", "Type of licensed clause-like unit lacking an overt verbal predicate.", "absolute_np_ap", "Her hands cold , Lily shivered", "Lily had cold hands", "verbless absolute clause", "classify the detached NP–AP absolute construction", "An ordinary NP with an attributive adjective is not a verbless clause."),
        ("clause_reduction_kind", "string", "Observed reduction of a subordinate clause's overt syntactic material.", "subject_and_copula_omission", "While tired , Lily worked", "While Lily was tired , she worked", "reduced adjectival subordinate clause", "record licensed omission of subject and copula", "Link the understood subject through the construction, not nearest-name heuristics."),
        ("extraposition_status", "string", "Whether a clause occurs after a dummy subject rather than in its canonical subject position.", "clausal_subject_extraposed", "It is clear that Lily left", "That Lily left is clear", "dummy-it clausal extraposition", "link the late clause to the subject-slot analysis", "Referential it remains possible in other constructions."),
        ("topicalization_status", "string", "Whether a clause contains a visible fronted noninterrogative topic.", "object_topic", "This book , Lily loved", "Lily loved this book", "object topicalization", "record the topic–gap relation as a clause-level construction", "Do not confuse a detached vocative with a fronted argument."),
        ("cleft_construction", "string", "Type of cleft syntax introducing an overt focused constituent.", "it_cleft", "It was Lily who left", "Lily left", "it-cleft with relative-like clause", "classify the cleft and identify its structural focus slot", "Cleft syntax supplies a focus construction, not a newly verified event."),
        ("clause_parallelism", "object", "Aligned grammatical slots shared by visibly parallel clauses.", {"first": ["subject", "verb", "object"], "second": ["subject", "verb", "object"]}, "Lily read a book and Ben wrote a letter", "Lily read while Ben slept", "parallel transitive clause coordination", "align matching syntactic slot sequences between conjuncts", "Parallel form does not imply equal event truth, time, or participants."),
    ]
    for key, typ, desc, value, pos, neg, construction, compute, guard in clause_rows:
        contract(key, typ, desc, f, value, pos, neg, construction, compute, guard=guard,
                 requires=("incremental_clause_analysis", "scope_stack"))
    assert len(c.attributes) == 224

    # 8. Questions, relatives, coordination: typed open dependencies.
    f = "interrogative_relative_coordination"
    question_lex = [
        ("relative_marker_form", "string", "Overt form class of a token already identified as a relative marker.", {"who": "human_pronoun", "which": "nonhuman_or_unrestricted_pronoun"}, "rel", ("and", "conj")),
        ("coordinator_type", "string", "Grammatical coordination operator supplied by an overt conjunction.", {"and": "conjunctive", "or": "disjunctive", "but": "adversative"}, "conj", "because"),
        ("interrogative_complementizer", "string", "Overt marker introducing a selected embedded interrogative clause.", {"whether": "whether", "if": "if"}, "comp", "that"),
    ]
    for key, typ, desc, mapping, pos, contrast in question_lex:
        lex(key, typ, desc, f, mapping, pos, contrast)
    question_pairs = [
        ("interrogative_form", "string", "Visible wh-clause form, retaining uncertainty between an independent question and an embedded interrogative.", "Who", "left", "subject_wh_clause_candidate", "the"),
        ("whether_if_embedding", "string", "Evidence of an embedded polar-question complement.", "wondered", "whether", "whether_clause", "that"),
        ("polar_question_marker", "string", "Overt auxiliary form opening a polar question with an overt subject.", "Did", "Lily", "do_inversion", "indeed"),
        ("pied_piping_status", "boolean", "Evidence that a preposition is fronted together with a wh-complement.", "To", "whom", True, "Lily"),
        ("correlative_coordination", "string", "Overt correlative construction prefix awaiting coordinated material.", "not", "only", "not_only_but_also_pending", "ever"),
    ]
    for key, typ, desc, left, right, value, contrast in question_pairs:
        pair(key, typ, desc, f, left, right, value, contrast,
             notes="Only visible construction evidence is projected; pending counterparts are expectations, not observed tokens.")
    question_rows = [
        ("question_gap_role", "string", "Grammatical argument role requested by an overt question dependency.", "object", "Which book did Lily read", "Which rabbit slept", "object wh-question", "identify the missing direct-object slot linked to the fronted wh phrase", "A subject wh-question has a different role despite similar vocabulary."),
        ("question_fronted_phrase_id", "string", "Node identifier of the overt fronted interrogative phrase.", "np1", "Which book did Lily read", "Lily read a book", "fronted wh-object phrase", "return the extracted interrogative NP node", "The node must be visible before the clause's gap is linked."),
        ("alternative_question_set", "array", "Visible syntactic alternatives presented by a question construction.", ["np1", "np2"], "Did Lily choose tea or coffee ?", "Lily chose tea and coffee", "alternative question", "collect the coordinated alternative phrase nodes", "Do not treat all disjunctions as questions."),
        ("echo_question_status", "boolean", "Whether a wh-expression remains in a position licensed as an echo-question construction.", True, "Lily bought what ?", "What did Lily buy ?", "in-situ echo question", "mark the nonfronted interrogative construction", "Question punctuation and an in-situ interrogative reading must both be supported."),
        ("tag_question_anchor", "string", "Clause identifier targeted by a following tag-question construction.", "cl1", "Lily left , didn't she ?", "Didn't Lily leave ?", "declarative plus question tag", "link the tag to its immediately preceding compatible host clause", "An independent negative question has no tag host."),
        ("relative_pronoun_id", "string", "Token anchor of an overt relative pronoun in a relative construction.", "t3", "the rabbit which hopped", "Which rabbit hopped ?", "noun-attached pronominal relative", "return the relative-pronoun anchor", "An interrogative pronoun is not a relative pronoun merely because it has the same form."),
        ("relative_head_id", "string", "Head-nominal node modified by an overt or zero relative clause.", "np1", "the book Lily read", "Lily read the book", "zero object relative modifying a noun", "return the nominal host of the relative", "Do not equate the relative's grammatical gap with an independently resolved entity."),
        ("relative_gap_role", "string", "Argument role left open inside the selected relative clause.", "subject", "the rabbit that hopped", "the rabbit that Lily saw", "subject relative", "identify the relative predicate's subject slot as linked to the nominal head", "Contrast object relatives even when the same relative marker is used."),
        ("relative_restrictiveness", "string", "Integrated versus supplementary syntactic status of the selected relative clause.", "supplementary", "Lily , who smiled ,", "the girl who smiled", "comma-delimited supplementary relative", "classify the relative attachment as supplementary", "Treat ambiguous punctuation and restrictive proper-name uses as alternatives."),
        ("relative_finiteness", "string", "Finiteness of a clause used as a nominal relative modifier.", "nonfinite_participial", "the rabbit hopping nearby", "the rabbit that hopped", "participial reduced relative", "classify the relative clause's verbal form as nonfinite", "Keep the nominal host and modifier separate from a matrix progressive clause."),
        ("free_relative_category", "string", "Syntactic category of a headless relative used as an argument or adjunct.", "NP", "Lily ate what Ben cooked", "What did Ben cook ?", "nominal free relative", "classify the entire relative as an NP-like argument", "Distinguish embedded content questions from free relatives by the selecting frame."),
        ("fused_relative_status", "boolean", "Whether one overt relative expression supplies both the nominal head and relative link.", True, "Whoever arrives may enter", "The person who arrives may enter", "fused head-relative construction", "mark the fused role of the initial relative expression", "An overt separate head noun blocks the fused-head analysis."),
        ("extraction_chain_id", "string", "Identifier linking a visible filler with its licensed syntactic gap.", "chain1", "Which book did Lily read", "Lily read the book", "wh filler–object-gap chain", "allocate a chain ID tied to the visible filler and compatible governor", "Do not create a gap solely to make an otherwise incompatible parse fit."),
        ("resumptive_pronoun_id", "string", "Anchor of an overt pronoun occupying a position associated with an earlier relative or topic.", "t8", "the rabbit that Lily said she saw it", "the rabbit that Lily saw", "resumptive object in a relative candidate", "record the overt resumptive anchor without deleting it", "Treat dialectal and disfluent resumptives descriptively; do not impose a universal grammaticality judgment."),
        ("relative_attachment_options", "array", "Nominal hosts still compatible with a visible relative attachment.", ["np_sister", "np_girl"], "the sister of the girl who smiled", "the girl who smiled", "ambiguous relative attachment across an of-phrase", "retain high and low nominal-host candidates", "Both hosts must satisfy the relative's grammatical constraints."),
        ("coordination_category", "string", "Shared syntactic category of coordinated constituents.", "VP", "Lily sang and danced", "Lily and Ben sang", "verb-phrase coordination", "classify the coordinated units by their common category", "Do not conflate coordinated subjects with coordinated predicates."),
        ("conjunct_head_ids", "array", "Ordered head anchors of the visible conjuncts in one coordination.", ["t1", "t3"], "Lily and Ben", "Lily met Ben", "nominal coordination", "collect the completed conjunct head anchors", "The conjunction must structurally join the two units."),
        ("coordination_shared_category", "string", "Syntactic category required by an incomplete later conjunct.", "NP", "Lily and", "Lily smiled", "unfinished NP coordination", "carry the first conjunct's category to the expected next conjunct", "Keep licensed unlike-category coordination as a separate construction candidate."),
        ("coordination_scope", "string", "Node identifier whose constituents are joined by the coordinator.", "np1", "Lily carried apples and pears", "Lily carried apples and Ben slept", "coordination inside an object NP", "return the coordinated NP node rather than the whole clause", "A following overt subject can license a wider clausal coordination instead."),
        ("gapping_alignment", "object", "Alignment between remnants and omitted grammatical slots in a gapping construction.", {"subject": "Ben", "object": "pears", "omitted_predicate": "ate"}, "Lily ate apples and Ben pears", "Lily ate apples and Ben ate pears", "verb gapping in a parallel clause", "align the visible remnants with the first clause's subject and object slots", "Require parallel syntax and retain alternatives when the remnant roles are ambiguous."),
        ("right_node_raising", "object", "Shared rightmost constituent linked to earlier coordinated incomplete constituents.", {"shared": "np_book", "slots": ["vp1.object", "vp2.object"]}, "Lily bought and Ben read the book", "Lily bought a book and Ben read a letter", "right-node-raised shared object", "link the final NP to each compatible open object slot", "Each conjunct must license the shared constituent category."),
        ("coordination_agreement_resolution", "object", "Grammatical agreement bundle supported by a coordinated subject construction.", {"number": "plural", "person": 3}, "Lily and Ben are", "Lily or Ben is", "and-coordinated third-person subject", "derive the coordinated subject's agreement bundle", "Do not apply additive plural agreement blindly to or-coordination."),
        ("discontinuous_coordination_state", "string", "Incremental status of a paired coordinator construction.", "awaiting_or_counterpart", "either Lily", "Lily", "open either–or coordination", "record the outstanding correlative counterpart", "The expectation must not be emitted as an already observed second coordinator."),
        ("coordination_ellipsis_source_id", "string", "Anchor of prior coordinated material that licenses omission in the current conjunct.", "vp1", "Lily will leave and Ben will too", "Ben will leave", "auxiliary VP ellipsis in a later conjunct", "retrieve the first conjunct's compatible VP source", "A matching auxiliary and a licensed antecedent are needed; do not copy across incompatible scope."),
    ]
    for key, typ, desc, value, pos, neg, construction, compute, guard in question_rows:
        contract(key, typ, desc, f, value, pos, neg, construction, compute, guard=guard,
                 requires=("incremental_constituent_analysis", "typed_gap_and_coordination_tracking"))
    assert len(c.attributes) == 256
    return c.records()

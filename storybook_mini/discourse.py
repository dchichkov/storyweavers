"""Reference realization with a two-sentence ambiguity window and speech deixis."""
from collections import Counter

OBJECT = {"she": "her", "he": "him", "they": "them", "it": "it"}
POSSESSIVE = {"she": "her", "he": "his", "they": "their", "it": "its"}
REFLEXIVE = {"she": "herself", "he": "himself", "they": "themselves", "it": "itself"}


class DiscourseHistory:
    def __init__(self, entities, enabled=True):
        self.entities = {e.id: e for e in entities}
        self.enabled = enabled
        self.seen = set()
        self.previous_subject = None
        self.previous_mentions = set()
        self.current_mentions = set()
        self.scene = None
        self.choices = []
        self.index = -1
        self.mentions = []
        self.last_seen = {}
        self.frequency = Counter()
        self.scene_start = 0
        self.owners_used = {}

    def start_sentence(self, scene):
        self.index += 1
        if scene != self.scene:
            self.previous_subject = None
            self.previous_mentions = set()
            self.scene_start = self.index
        self.scene = scene
        self.current_mentions = set()

    def rivals(self, eid, competitors=()):
        recent = set().union(*self.mentions[max(self.scene_start, self.index - 2):]) if self.mentions else set()
        recent |= self.current_mentions | set(competitors)
        return {other for other in recent if other != eid and
                self.entities[other].pronoun == self.entities[eid].pronoun}

    def refer(self, eid, role, fact_id, competitors=(), force_name=False, *,
              owner="", binding="", scope="narration", speaker="", listener="", possessive=True):
        ent = self.entities[eid]
        grammatical_role = role.split(".")[-1]
        rivals = self.rivals(eid, competitors)
        distance = self.index - self.last_seen[eid] if eid in self.last_seen else None
        use_pronoun, reason = False, "full_reference"
        if scope == "speech" and eid in {speaker, listener}:
            phrase = (("we" if ent.number == "plural" else "I") if grammatical_role == "subject"
                      else ("us" if ent.number == "plural" else "me")) if eid == speaker else "you"
            if grammatical_role in {"object", "target"} and eid == binding:
                phrase = ("ourselves" if ent.number == "plural" else "myself") if eid == speaker else (
                    "yourselves" if ent.number == "plural" else "yourself")
            use_pronoun, reason = True, "speaker_deixis" if eid == speaker else "hearer_deixis"
        elif grammatical_role in {"object", "target"} and eid == binding:
            # Reflexives remain necessary in discourse ablations.
            phrase, reason, use_pronoun = REFLEXIVE[ent.pronoun], "reflexive_binding", True
        else:
            locally_clear = eid in self.current_mentions and not any(
                other != eid and self.entities[other].pronoun == ent.pronoun
                for other in self.current_mentions | set(competitors))
            use_pronoun = (self.enabled and not force_name and scope == "narration" and (
                (grammatical_role == "subject" and self.previous_subject == eid and not rivals)
                or (grammatical_role == "object" and eid in self.seen and (
                    locally_clear or (distance is not None and distance <= 1 and not rivals
                                      and self.last_seen[eid] >= self.scene_start)))))
            if use_pronoun:
                phrase = OBJECT[ent.pronoun] if grammatical_role == "object" else ent.pronoun
                reason = "local_antecedent" if locally_clear else "recent_unambiguous_antecedent"
            elif ent.name:
                phrase = ent.name
                reason = "ambiguous_antecedent" if rivals else "focus_or_boundary"
            else:
                noun = ent.noun
                if self.enabled and eid in self.seen and ent.short_noun:
                    if not any(e.id != eid and e.id in self.seen and
                               (e.short_noun or e.noun) == ent.short_noun for e in self.entities.values()):
                        noun = ent.short_noun
                if self.enabled and owner and possessive and (eid not in self.seen or
                        self.owners_used.get(eid) != owner or
                        (scope == "speech" and owner in {speaker, listener})):
                    possessor = self.entities[owner]
                    if scope == "speech" and owner in {speaker, listener}:
                        determiner = ("our" if self.entities[owner].number == "plural" else "my") if owner == speaker else "your"
                    elif owner == binding and not self.rivals(owner, competitors):
                        determiner = POSSESSIVE[possessor.pronoun]
                    else:
                        determiner = (possessor.name or "the " + possessor.noun) + "’s"
                    phrase, reason = f"{determiner} {noun}", "grounded_possessor"
                else:
                    determiner = "the"
                    if self.enabled and eid not in self.seen and not ent.definite:
                        determiner = "some" if ent.mass or ent.number == "plural" else (
                            "an" if ent.noun[0].lower() in "aeiou" else "a")
                        if ent.noun in {"wind", "evening sky"}:
                            determiner = "the"
                    phrase = f"{determiner} {noun}"
                    reason = "first_mention" if eid not in self.seen else "known_entity"
        self.choices.append({"fact_id": fact_id, "entity": eid, "role": role,
                             "text": phrase, "pronoun": use_pronoun, "reason": reason,
                             "scope": scope, "distance": distance,
                             "frequency_before": self.frequency[eid], "rivals": sorted(rivals),
                             "owner": owner})
        self.seen.add(eid)
        self.frequency[eid] += 1
        if owner:
            self.owners_used[eid] = owner
        if scope == "narration":
            self.current_mentions.add(eid)
            self.last_seen[eid] = self.index
        return phrase

    def elide(self, eid, role, fact_id, reason="shared_subject"):
        self.choices.append({"fact_id": fact_id, "entity": eid, "role": role,
                             "text": "", "pronoun": False, "ellipsis": True, "reason": reason,
                             "scope": "narration"})
        self.seen.add(eid)
        self.current_mentions.add(eid)
        self.last_seen[eid] = self.index

    def end_sentence(self, subject, dialogue=False):
        self.previous_subject = None if dialogue else subject
        self.previous_mentions = self.current_mentions.copy()
        self.mentions.append(self.current_mentions.copy())

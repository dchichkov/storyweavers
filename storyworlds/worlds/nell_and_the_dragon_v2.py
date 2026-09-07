#!/usr/bin/env python3
"""A small goal-directed Nell world with independently seeded tellings.

Characters act on their own knowledge. Physical effects produce an event trace;
the renderer can retell that trace but cannot change it. No LLM runs here.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field, replace
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


USES = ("display", "support")
OWNERS = ("dragon", "bird")
SUPPLIES = ("nearby", "home", "raw")
TEMPERS = ("proud", "careful")
VOICES = ("plain", "dry", "playful")
DIALOGUE_LEVELS = ("spare", "balanced", "conversational")
DETAIL_LEVELS = ("compact", "normal", "rich")
NAMES = ("Nell", "Ada", "Kit", "Rose")
JEWELS = {"emerald": "green", "sapphire": "blue", "amethyst": "purple"}
MAX_ACTIONS = 24
SAFE_DISTANCE = 8


@dataclass
class StoryParams:
    hero: str = "Nell"
    jewel: str = "emerald"
    use: str = "display"
    owner: str = "dragon"
    supplies: str = "nearby"
    temper: str = "proud"
    nest_slots: int = 1
    world_seed: int = 777
    prose_seed: int = 42
    voice: str = "dry"
    dialogue_level: str = "conversational"
    detail_level: str = "normal"
    flourish_budget: int = 2


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = "clearing"
    owner: str = "nell"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Action:
    kind: str
    actor: str
    target: str = ""


@dataclass(frozen=True)
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]
    state: dict


@dataclass
class Rendering:
    story: str
    qa: list[QAItem]
    evidence: dict[str, int]
    qa_evidence: list[list[str]]
    flourishes: int
    dialogue_turns: int


def validate_params(p: StoryParams):
    for value, registry, label in ((p.use, USES, "use"), (p.owner, OWNERS, "owner"),
            (p.supplies, SUPPLIES, "supplies"), (p.temper, TEMPERS, "temper"),
            (p.jewel, JEWELS, "jewel"), (p.voice, VOICES, "voice"),
            (p.dialogue_level, DIALOGUE_LEVELS, "dialogue level"), (p.detail_level, DETAIL_LEVELS, "detail level")):
        if value not in registry:
            raise StoryError(f"Unknown {label}: {value!r}.")
    if type(p.nest_slots) is not int or p.nest_slots not in (1, 2):
        raise StoryError("The nest must have one or two display spaces.")
    if type(p.flourish_budget) is not int or not 0 <= p.flourish_budget <= 5:
        raise StoryError("Flourish budget must be an integer from 0 to 5.")
    if any(type(seed) is not int for seed in (p.world_seed, p.prose_seed)):
        raise StoryError("Seeds must be integers.")
    if not re.fullmatch(r"[A-Z][a-z]+", p.hero):
        raise StoryError("Use a simple capitalized name, such as Nell.")


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.rng = random.Random(params.world_seed)
        self.entities: dict[str, Entity] = {}
        self.relations: set[tuple[str, str, str]] = set()
        self.history: list[Event] = []
        self.fact_events: dict[str, int] = {}
        self.outcome = ""

    def snapshot(self) -> dict:
        return dict(entities={key: asdict(value) for key, value in self.entities.items()},
                    relations=sorted(self.relations), outcome=self.outcome)

    def record(self, kind: str, actor: str, *, facts=(), needs=(), **data):
        if any(fact not in self.fact_events for fact in needs):
            raise StoryError(f"{kind} refers to evidence that has not occurred.")
        event_id = len(self.history)
        causes = tuple(sorted({self.fact_events[fact] for fact in needs}))
        self.history.append(Event(id=event_id, kind=kind, actor=actor, data=data,
                                  facts=tuple(facts), causes=causes, state=self.snapshot()))
        for fact in facts:
            self.fact_events[fact] = event_id


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(p)
    material_location = "home" if p.supplies == "home" else "pocket"
    raw = p.supplies == "raw"
    w.entities = {
        "nell": Entity(id="nell", label=p.hero, kind="character", memes={"curiosity": 1},
                       goals=["understand_claim", "protect_nest"], beliefs={"claim": "dragon_wants_jewel"}),
        "dragon": Entity(id="dragon", label="the dragon", kind="character", owner="dragon",
                         meters={"distance": 3, "teeth": 1, "volume": 1, "reach": 12, "claw_width": 8},
                         memes={"pride": 1 if p.temper == "proud" else 0.2, "patience": 0, "relief": 0},
                         beliefs={"jewel_source": "gift" if p.owner == "bird" else "windowsill",
                                  "claim": "recover_jewel", "ruby_works": "yes"}, goals=["recover_jewel"]),
        "bird": Entity(id="bird", label="the magpie", kind="character", location="nest", owner="bird",
                       meters={"capacity": 2}, memes={"fear": 1}, beliefs={"use": p.use}, goals=["keep_home", "decorate"]),
        "jewel": Entity(id="jewel", label=p.jewel, location="nest", owner=p.owner, meters={"mass": 1, "shine": 3}),
        "ruby": Entity(id="ruby", label="the cabbage-sized ruby", location="dragon_claw", owner="dragon",
                       meters={"mass": 20, "shine": 9}),
        "tree": Entity(id="tree", label="the narrow pine", owner="", meters={"intact": 1, "fork_width": 2}),
        "nest": Entity(id="nest", label="the nest", location="tree", owner="bird",
                       meters={"intact": 1, "load": 2, "needs_prop": int(p.use == "support"), "slots": p.nest_slots}),
        "button": Entity(id="button", label="the brass button", location=material_location,
                         meters={"mass": 1, "shine": 1 if raw else 6}),
        "brace": Entity(id="brace", label="the wooden brace", location=material_location,
                        meters={"mass": 1, "strength": 0 if raw else 3, "assembled": 0 if raw else 1}),
        "stick": Entity(id="stick", label="the short straight stick", location="pocket", meters={"strength": 3}),
        "cord": Entity(id="cord", label="the soft cord", location="pocket", meters={"length": 3}),
        "cloth": Entity(id="cloth", label="the polishing cloth", location="pocket"),
        "dish": Entity(id="dish", label="the tin dish", location="pocket"),
    }
    if p.use == "support":
        w.relations.add(("jewel", "supports", "nest"))
    else:
        w.relations.add(("jewel", "decorates", "nest"))
    w.record("opening", "dragon", facts=("request", "nest_location"), hero=p.hero, jewel=p.jewel, color=JEWELS[p.jewel])
    return w


def safe_space(w: World) -> bool:
    d = w.entities["dragon"].meters
    return d["distance"] >= SAFE_DISTANCE and not d["teeth"] and not d["volume"]


def supported(w: World, *, without=()) -> bool:
    if not w.entities["nest"].meters["needs_prop"]:
        return True
    strengths = {"jewel": 2, "dragon": 3, "brace": w.entities["brace"].meters["strength"]}
    return any(predicate == "supports" and target == "nest" and source not in without
               and strengths.get(source, 0) >= w.entities["nest"].meters["load"]
               for source, predicate, target in w.relations)


def can_detach(w: World) -> bool:
    return w.entities["jewel"].owner == "dragon" and supported(w, without=("jewel",))


def material_ready(w: World, target: str) -> bool:
    ent = w.entities[target]
    if ent.location not in ("pocket", "dish"):
        return False
    return ent.meters["shine"] > w.entities["jewel"].meters["shine"] if target == "button" else bool(ent.meters["assembled"])


def choose_action(w: World) -> Action:
    """A bounded domain policy, not an omniscient search or a fixed scene list."""
    n, d, b, j = (w.entities[key] for key in ("nell", "dragon", "bird", "jewel"))
    facts = w.fact_events
    if w.outcome:
        return Action(kind="close", actor="dragon")
    if j.location == "falling":
        return Action(kind="catch", actor="dragon")
    if j.location == "dish":
        return Action(kind="collect", actor="dragon")
    if j.location == "dragon_claw":
        if ("dragon", "supports", "nest") in w.relations:
            return Action(kind="withdraw_support", actor="dragon")
        raise StoryError("A recovered jewel needs a recorded resolution.")
    # Carrying and installing are the bird's choices, not Nell's access to its mind.
    if b.beliefs.get("carrying"):
        return Action(kind="carry" if b.location == "dish" else "install", actor="bird", target=b.beliefs["carrying"])
    if n.beliefs.get("origin") == "gift":
        return Action(kind="honor_gift", actor="nell")
    pending = []
    if "origin" not in n.beliefs:
        pending.append(Action(kind="ask_history", actor="nell"))
    if "use" not in n.beliefs:
        pending.append(Action(kind="observe", actor="nell"))
    if d.memes["pride"] > .7 and "ruby_refused" not in facts:
        pending.append(Action(kind="try_ruby", actor="dragon"))
    if pending:
        return w.rng.choice(pending)
    target = "brace" if n.beliefs["use"] == "support" else "button"
    if "material" not in n.beliefs:
        return Action(kind="inspect_material", actor="nell", target=target)
    if w.entities[target].location == "home":
        return Action(kind="fetch", actor="nell", target=target)
    if "material_ready" not in facts:
        return Action(kind="prepare_material", actor="nell", target=target)
    if not safe_space(w):
        return Action(kind="make_space", actor="dragon")
    if target == "brace" and "temporary_support" not in facts:
        return Action(kind="steady", actor="dragon")
    if "offer_present" not in facts:
        return Action(kind="offer", actor="nell", target=target)
    if "offer_installed" not in facts:
        return Action(kind="take", actor="bird", target=target)
    if "kept_both" in facts and "return_requested" not in facts:
        return Action(kind="request_return", actor="nell")
    return Action(kind="release", actor="bird")


def execute(w: World, action: Action):
    """Actions validate actual prerequisites; an observed setback is an event."""
    n, d, b, j = (w.entities[key] for key in ("nell", "dragon", "bird", "jewel"))
    k, target = action.kind, action.target
    expected = {"ask_history": "nell", "observe": "nell", "try_ruby": "dragon", "honor_gift": "nell",
                "inspect_material": "nell", "fetch": "nell", "prepare_material": "nell", "make_space": "dragon",
                "steady": "dragon", "offer": "nell", "take": "bird", "carry": "bird", "install": "bird",
                "request_return": "nell", "release": "bird", "catch": "dragon", "collect": "dragon",
                "withdraw_support": "dragon", "close": "dragon"}
    if expected.get(k) != action.actor:
        raise StoryError("This action is not available to that character.")
    if "ending" in w.fact_events or (w.outcome and k != "close"):
        raise StoryError("The conflict is already resolved.")

    def require(condition, message):
        if not condition:
            raise StoryError(message)

    if k == "ask_history":
        require("origin" not in n.beliefs, "That question was already answered.")
        n.beliefs["origin"] = d.beliefs["jewel_source"]
        w.record(k, action.actor, facts=("origin_known",), needs=("request",), origin=n.beliefs["origin"])
    elif k == "observe":
        require("use" not in n.beliefs, "The use is already understood.")
        # Observe a visible relationship, not the bird's private preference field.
        n.beliefs["use"] = "support" if ("jewel", "supports", "nest") in w.relations else "display"
        w.record(k, action.actor, facts=("use_known",), needs=("nest_location",), use=n.beliefs["use"])
    elif k == "try_ruby":
        require("ruby_refused" not in w.fact_events, "Do not repeat an already disproved offer.")
        require(w.entities["ruby"].meters["mass"] > b.meters["capacity"], "This ruby is not an uncarryable offer.")
        d.beliefs["ruby_works"] = "no"
        d.memes["pride"] = .5
        b.memes["fear"] = float(not safe_space(w))
        n.beliefs["ruby_problem"] = "too_large"
        w.record("ruby_refused", action.actor, facts=("ruby_refused",), needs=("request",), fear=bool(b.memes["fear"]))
    elif k == "honor_gift":
        require(n.beliefs.get("origin") == "gift" and j.owner == "bird", "The gift must be established, not invented.")
        d.goals = ["honor_gift"]
        d.beliefs["claim"] = "gift_belongs_to_bird"
        d.memes.update(pride=.2, relief=1)
        w.outcome = "gift_honored"
        w.record(k, action.actor, facts=("conflict_resolved",), needs=("origin_known",), outcome=w.outcome)
    elif k == "inspect_material":
        require(n.beliefs.get("origin") == "windowsill" and "use" in n.beliefs, "Understand the claim and use before choosing equipment.")
        require(target == ("brace" if n.beliefs["use"] == "support" else "button"), "That material does not address the observed need.")
        n.beliefs["material"] = target
        n.beliefs["material_location"] = w.entities[target].location
        w.record(k, action.actor, facts=("material_known",), needs=("use_known", "origin_known"),
                 target=target, location=w.entities[target].location, ready=material_ready(w, target))
    elif k == "fetch":
        require(n.beliefs.get("material") == target and w.entities[target].location == "home", "Fetch a known material that is actually at home.")
        w.entities[target].location = "pocket"
        n.beliefs["material_location"] = "pocket"
        w.record(k, action.actor, facts=("material_fetched",), needs=("material_known",), target=target)
    elif k == "prepare_material":
        require(n.beliefs.get("material") == target and w.entities[target].location == "pocket", "The material must be identified and available.")
        needs = ("material_known",) + (("material_fetched",) if "material_fetched" in w.fact_events else ())
        if material_ready(w, target):
            w.record("ready_material", action.actor, facts=("material_ready",), needs=needs, target=target)
        elif target == "button":
            require(w.entities["cloth"].location == "pocket", "Polishing needs the cloth.")
            w.entities[target].meters["shine"] = 6
            w.record("polish", action.actor, facts=("material_ready",), needs=needs, target=target)
        else:
            require(all(w.entities[key].location == "pocket" for key in ("stick", "cord")), "Building the brace needs both a stick and cord.")
            require(w.entities["cord"].meters["length"] >= 2, "The cord must reach both attachment points.")
            for key in ("stick", "cord"):
                w.entities[key].location = "brace"
            w.entities[target].meters.update(assembled=1, strength=w.entities["stick"].meters["strength"])
            w.record("assemble", action.actor, facts=("material_ready",), needs=needs, target=target)
    elif k == "make_space":
        require(not safe_space(w), "The approach is already clear.")
        d.meters.update(distance=SAFE_DISTANCE, teeth=0, volume=0)
        d.memes["patience"] = 1
        b.memes["fear"] = 0
        w.record(k, action.actor, facts=("safe_space",), needs=("request",))
    elif k == "steady":
        require(n.beliefs.get("use") == "support" and safe_space(w), "Recognize the structural problem and calm the bird first.")
        require(("jewel", "supports", "nest") in w.relations, "There is no load for the dragon to take.")
        w.relations.add(("dragon", "supports", "nest"))
        w.record(k, action.actor, facts=("temporary_support",), needs=("use_known", "safe_space"))
    elif k == "offer":
        require(n.beliefs.get("material") == target and material_ready(w, target), "An offer must be useful and physically ready.")
        require(safe_space(w) and "offer_present" not in w.fact_events, "Set one offer in a clear space.")
        if target == "brace":
            require(("dragon", "supports", "nest") in w.relations, "Steady the branch before inviting the repair.")
        w.entities["dish"].location = "ground"
        w.entities[target].location = "dish"
        needs = ("material_ready", "safe_space") + (("temporary_support",) if target == "brace" else ())
        w.record(k, action.actor, facts=("offer_present",), needs=needs, target=target)
    elif k == "take":
        require(target in ("button", "brace") and w.entities[target].location == "dish", "The object must be in the dish.")
        require(safe_space(w), "The bird cannot approach the nearby open mouth.")
        item = w.entities[target]
        useful = item.meters.get("shine", 0) > j.meters["shine"] if b.beliefs["use"] == "display" else item.meters.get("strength", 0) >= w.entities["nest"].meters["load"]
        require(item.meters["mass"] <= b.meters["capacity"] and useful, "The bird will not take an unusable item.")
        item.location, item.owner = "beak", "bird"
        b.location = "dish"
        b.beliefs["carrying"] = target
        w.record(k, action.actor, facts=("offer_taken",), needs=("offer_present",), target=target)
    elif k == "carry":
        require(b.location == "dish" and b.beliefs.get("carrying") == target, "The bird must be carrying the object from the dish.")
        b.location = "nest"
        w.record(k, action.actor, facts=("offer_at_nest",), needs=("offer_taken",), target=target)
    elif k == "install":
        require(b.location == "nest" and b.beliefs.get("carrying") == target and w.entities[target].location == "beak", "Installation requires arrival with the object.")
        if target == "brace":
            require(("dragon", "supports", "nest") in w.relations and supported(w, without=("jewel",)), "The nest needs temporary support during the repair.")
        w.entities[target].location = "nest"
        del b.beliefs["carrying"]
        if target == "brace":
            w.relations.add((target, "supports", "nest"))
            w.record("install_brace", action.actor, facts=("offer_installed",), needs=("offer_at_nest", "temporary_support"), target=target)
        else:
            w.relations.add((target, "decorates", "nest"))
            if w.entities["nest"].meters["slots"] == 1:
                w.relations.remove(("jewel", "decorates", "nest"))
                j.location = "falling"
                w.record("replace_ornament", action.actor, facts=("offer_installed", "jewel_released"), needs=("offer_at_nest",), target=target)
            else:
                w.record("keep_both", action.actor, facts=("offer_installed", "kept_both"), needs=("offer_at_nest",), target=target)
    elif k == "request_return":
        require("kept_both" in w.fact_events and j.owner == "dragon", "Taking a gift alone is not a promise to return something.")
        b.beliefs["return_cue"] = "jewel_to_empty_dish"
        w.record(k, action.actor, facts=("return_requested",), needs=("kept_both", "origin_known"))
    elif k == "release":
        require(j.location == "nest" and j.owner == "dragon" and "offer_installed" in w.fact_events, "Do not release a jewel before the replacement is installed.")
        require(can_detach(w), "Removing the jewel would collapse the nest or violate its ownership.")
        require(supported(w, without=("jewel", "dragon")), "The replacement must bear the load independently before returning the jewel.")
        if b.beliefs["use"] == "display":
            require(b.beliefs.get("return_cue") == "jewel_to_empty_dish", "The bird has not been shown what to return.")
        w.relations.discard(("jewel", "supports", "nest"))
        w.relations.discard(("jewel", "decorates", "nest"))
        j.location = "dish"
        needs = ("offer_installed",) + (("return_requested",) if b.beliefs["use"] == "display" else ())
        w.record(k, action.actor, facts=("jewel_released",), needs=needs, use=b.beliefs["use"])
    elif k in ("catch", "collect"):
        require(j.location == ("falling" if k == "catch" else "dish") and j.owner == "dragon", "Recover only a released jewel that belongs to the dragon.")
        require(d.meters["distance"] <= d.meters["reach"], "The jewel is beyond the dragon's reach.")
        j.location = "dragon_claw"
        d.memes["relief"] = 1
        if ("dragon", "supports", "nest") not in w.relations:
            w.outcome = "exchange" if "kept_both" not in w.fact_events else "requested_return"
        w.record(k, action.actor, facts=("jewel_recovered",), needs=("jewel_released",))
    elif k == "withdraw_support":
        require(j.location == "dragon_claw" and ("dragon", "supports", "nest") in w.relations, "The dragon is not finishing a supported recovery.")
        require(supported(w, without=("jewel", "dragon")), "The permanent brace must bear the load by itself.")
        w.relations.remove(("dragon", "supports", "nest"))
        w.outcome = "cooperative_repair"
        w.record(k, action.actor, facts=("support_tested", "conflict_resolved"), needs=("offer_installed", "jewel_recovered"))
    elif k == "close":
        require(bool(w.outcome), "A closing promise must not hide an unresolved conflict.")
        d.goals = ["tell_true_story"]
        d.beliefs["payment"] = "promised_true_story"
        n.goals = ["ask_questions"]
        n.location = d.location = "path_home"
        needs = ("conflict_resolved",) if "conflict_resolved" in w.fact_events else ("jewel_recovered",)
        w.record(k, action.actor, facts=("payment_promised", "ending"), needs=needs, outcome=w.outcome)


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_ACTIONS):
        execute(w, choose_action(w))
        if "ending" in w.fact_events:
            validate_world(w)
            return w
    raise StoryError("The bounded policy did not resolve the conflict.")


def validate_world(w: World):
    j = w.entities["jewel"]
    if not w.outcome or "ending" not in w.fact_events:
        raise StoryError("The story needs a resolved conflict and ending.")
    if w.outcome == "gift_honored":
        if j.location != "nest" or j.owner != "bird":
            raise StoryError("Honoring the gift must leave it with its owner.")
    elif j.location != "dragon_claw" or j.owner != "dragon":
        raise StoryError("Recovery must return the actual jewel.")
    if not supported(w) or ("dragon", "supports", "nest") in w.relations:
        raise StoryError("The nest must be independently supported at the end.")
    if any(w.entities[key].meters["intact"] != 1 for key in ("nest", "tree")):
        raise StoryError("The home must remain intact.")
    if w.entities["dragon"].beliefs.get("payment") != "promised_true_story":
        raise StoryError("The story payment has not been promised.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on a future event.")


def trace_signature(w: World, *, causal=False) -> str:
    if causal:
        # Ignore cosmetic slots and independent-event ordering, retain dependencies.
        value = sorted((e.kind, e.actor, tuple(sorted(w.history[i].kind for i in e.causes))) for e in w.history)
    else:
        value = [asdict(e) for e in w.history]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class Teller:
    def __init__(self, trace: list[Event], p: StoryParams):
        self.trace, self.params = trace, p
        self.rng = random.Random(p.prose_seed)
        self.context = dict(trace[0].data)
        self.paragraphs: list[str] = []
        self.evidence: dict[str, int] = {}
        self.qa: list[QAItem] = []
        self.qa_evidence: list[list[str]] = []
        self.flourishes = self.turns = 0
        self.used_flourishes: set[str] = set()

    def choose(self, *choices):
        if len(choices) > 2 and self.params.detail_level != "normal":
            ranked = sorted(choices, key=lambda value: len(value.split()))
            choices = ranked[:2] if self.params.detail_level == "compact" else ranked[-2:]
        return self.rng.choice(choices).format(**self.context)

    def tell(self, *choices):
        self.paragraphs.append(self.choose(*choices))

    def exchange(self, lines: tuple[tuple[str, str], ...]):
        paragraphs = []
        for index, (speaker, line) in enumerate(lines):
            line = line.format(**self.context)
            if index == 0 or (index and lines[index - 1][0] == speaker):
                tag = "asked" if line.endswith("?") else "said"
                name = self.context["hero"] if speaker == "nell" else "the dragon"
                if line.endswith(".") and not line.endswith("..."):
                    line = line[:-1] + ","
                paragraphs.append(f'"{line}" {name} {tag}.')
            else:
                paragraphs.append(f'"{line}"')
        self.turns += len(lines)
        self.paragraphs.extend(paragraphs)

    def dialogue(self, variants, *, optional=False):
        if optional and (self.params.dialogue_level == "spare" or
                         (self.params.dialogue_level == "balanced" and self.rng.random() < .5)):
            return
        self.exchange(self.rng.choice(variants))

    def flourish(self, key, variants):
        if self.params.detail_level == "compact" or self.flourishes >= self.params.flourish_budget or key in self.used_flourishes:
            return
        probability = .95 if self.params.detail_level == "rich" else .55
        if self.rng.random() < probability:
            self.tell(*variants)
            self.used_flourishes.add(key)
            self.flourishes += 1

    def question(self, event: Event, question: str, answer: str):
        self.qa.append(QAItem(question=question.format(**self.context), answer=answer.format(**self.context)))
        self.qa_evidence.append(list(event.facts))

    def run(self) -> Rendering:
        for event in self.trace:
            self.render_event(event)
            for fact in event.facts:
                self.evidence[fact] = event.id
        if any(fact not in self.evidence for group in self.qa_evidence for fact in group):
            raise StoryError("A QA answer relies on an omitted event.")
        return Rendering(story="\n\n".join(self.paragraphs), qa=self.qa, evidence=self.evidence,
                         qa_evidence=self.qa_evidence, flourishes=self.flourishes, dialogue_turns=self.turns)

    def render_event(self, event: Event):
        k, data, voice = event.kind, event.data, self.params.voice
        target = data.get("target", "button")
        self.context["material"] = "brass button" if target == "button" else "wooden brace"
        if k == "opening":
            self.tell("At half past four, a dragon arrived at {hero}'s window. She was reading.",
                      "{hero} was reading when a dragon's face appeared outside her window. It was half past four.",
                      "The clock had just struck half past four when the dragon came to {hero}'s window. Her book lay open.")
            requests = {
                "plain": ((("dragon", "Will you help me get my {jewel} back?"), ("nell", "Where is it?")),
                          (("dragon", "I need help finding a way to retrieve my {jewel}."), ("nell", "Tell me where to look."))),
                "dry": ((("dragon", "I require a thief."), ("nell", "Would someone who asks questions do?")),
                        (("dragon", "My {jewel} has changed address."), ("nell", "Did you help it move?"))),
                "playful": ((("dragon", "I have a rather small problem."), ("nell", "How small?"), ("dragon", "One {jewel}.")),
                            (("dragon", "Can you rescue a treasure?"), ("nell", "Does it need rescuing?"), ("dragon", "I was hoping you wouldn't start there."))),
            }
            self.dialogue(requests[voice])
            self.tell("The pea-sized {jewel} was in a magpie's nest, high in a narrow pine. The dragon's claw could reach it, but would break the branches.",
                      "They went to a narrow pine. A magpie had the pea-sized {jewel} in her nest. The dragon could reach the nest; his great claw could not fit inside without breaking its branches.")
            self.question(event, "Why did the dragon need help?", "The {jewel} was in a magpie's nest in a narrow pine. His claw could reach it, but taking it that way would break the branches.")
        elif k == "ask_history":
            self.tell("{hero} asked how the jewel had reached the tree.",
                      "Before calling anyone a thief, {hero} wanted to know where the jewel had been.",
                      "{hero} asked the dragon to start with the last place he had seen his treasure.")
            if data["origin"] == "gift":
                self.dialogue(((("dragon", "I left it for her. There was a note: 'Keep it.'"),
                                ("nell", "Did you mean that?"), ("dragon", "At the time.")),
                               (("dragon", "I gave it to her with a note saying she could keep it."),
                                ("nell", "And now you want it back?"), ("dragon", "It is a very nice {jewel}."))))
                self.question(event, "How had the magpie obtained the jewel?", "The dragon had given it to her with a note saying she could keep it. {hero} learned this by asking him what had happened.")
            else:
                self.dialogue(((("dragon", "It was on my windowsill. I saw her carry it away, but I hadn't given it to her."),
                                ("nell", "Then we know how it got here.")),
                               (("dragon", "She lifted it from my windowsill. I hadn't given it to her."),
                                ("nell", "We'll try to get it back without breaking her home."))))
                self.question(event, "How had the jewel reached the nest?", "The dragon saw the magpie take it from his windowsill. He told {hero} that he had not given it to her.")
        elif k == "observe":
            if data["use"] == "support":
                self.tell("{hero} watched the loose rim of the nest settle against the {jewel}. The stone was holding it up.",
                          "A twig shifted at the nest's edge. The rim sagged until it rested on the {jewel}; {hero} saw what was carrying its weight.",
                          "The magpie pushed at a loose part of the rim. It stayed up only where the {jewel} lay beneath it. {hero} watched that spot carefully.")
                self.dialogue(((("nell", "That's a prop, not just a treasure."), ("dragon", "A very expensive prop.")),
                               (("nell", "Take the stone away and the rim will sag."), ("dragon", "Then we need something to put in its place."))), optional=True)
                self.question(event, "What was the jewel doing in the nest?", "It was supporting a loose section of the nest's rim. {hero} saw how the loose rim rested on the stone.")
            else:
                self.tell("The magpie turned the {jewel} toward the sun. {hero} watched the {color} light catch along its edge.",
                          "The bird adjusted the {jewel} on the nest's rim until it shone. {hero} noticed that she was arranging a decoration.",
                          "{hero} watched the magpie fuss over her bright ornament, turning it this way and that to catch the light.")
                self.dialogue(((("nell", "She likes the shine."), ("dragon", "We have that in common.")),
                               (("nell", "She's decorating."), ("dragon", "I hadn't thought of myself as a supplier."))), optional=True)
                self.question(event, "What did the magpie like about the jewel?", "She used it as a bright decoration on her nest. {hero} watched her turn it to catch the light.")
        elif k == "ruby_refused":
            self.tell("The dragon offered a ruby the size of a cabbage. It was far too big for the magpie to carry.",
                      "He opened his claw to offer a cabbage-sized ruby. {hero} compared it with the little bird: she could never lift it.",
                      "The dragon presented his ruby. It was as large as a cabbage and much too heavy for the bird.")
            if data["fear"]:
                self.tell("The magpie stayed among the branches, away from his mouth.",
                          "With the dragon so close, the magpie would not come down.")
            exchanges = {
                "plain": ((("dragon", "It is worth a kingdom."), ("nell", "But she can't carry it.")),
                          (("dragon", "Surely this is enough."), ("nell", "It needs to be small enough for her to use."))),
                "dry": ((("dragon", "It is worth a kingdom."), ("nell", "She hasn't got a kingdom-sized pocket.")),
                        (("dragon", "A magnificent offer."), ("nell", "For someone considerably larger."))),
                "playful": ((("dragon", "Look how it sparkles!"), ("nell", "She would need a cart to take it home.")),
                            (("dragon", "I chose a generous one."), ("nell", "You could be a little less generous in every direction."))),
            }
            self.dialogue(exchanges[voice])
            self.flourish("ruby", ("The ruby shone in the enormous claw.",) if voice == "plain" else
                          ("The ruby was magnificently unhelpful.", "All that value, and still too much ruby."))
            self.question(event, "Why did the ruby offer fail?", "The ruby was cabbage-sized, too big and heavy for the magpie to carry. Its value did not make it usable by such a small bird.")
        elif k == "honor_gift":
            exchanges = {
                "plain": ((("nell", "You gave it to her. It belongs to her now."), ("dragon", "Then I'll leave it with her.")),
                          (("nell", "She kept your gift, just as your note asked."), ("dragon", "You're right. She should keep it."))),
                "dry": ((("nell", "Keeping a gift isn't stealing."), ("dragon", "Even a particularly good gift?"),
                          ("nell", "Particularly that one."), ("dragon", "Then it stays.")),
                        (("nell", "Your note seems to have worked."), ("dragon", "Rather better than I intended."),
                         ("nell", "Will you let her keep it?"), ("dragon", "Yes. A gift should stay a gift."))),
                "playful": ((("nell", "You can't send a gift and then chase it home."), ("dragon", "Not even politely?"),
                              ("nell", "Let it stay."), ("dragon", "All right. It has a home here.")),
                            (("nell", "She followed your note exactly."), ("dragon", "An excellent listener, then."),
                             ("nell", "Can you be one too?"), ("dragon", "Yes. She can keep the jewel."))),
            }
            self.dialogue(exchanges[voice])
            self.tell("He stopped asking for the jewel back. It stayed in the magpie's nest.",
                      "The dragon accepted that the {jewel} belonged to the magpie. He left it where it was.")
            self.question(event, "Why did the dragon leave the jewel in the nest?", "He had given it to the magpie and told her to keep it. After {hero} pointed this out, he accepted that it was hers and stopped trying to recover it.")
        elif k == "inspect_material":
            if data["location"] == "home":
                self.tell("{hero} knew where to find a {material}, but it was back at home.",
                          "A {material} would help. Unfortunately, {hero} had left hers at home.")
                self.dialogue(((("dragon", "Must we go all the way back?"), ("nell", "Unless you brought one.")),
                               (("dragon", "I brought a ruby."), ("nell", "That's not the thing we're missing."))), optional=True)
            elif data["ready"]:
                self.tell("{hero} found a {material} in her pocket.", "A {material} turned up when {hero} checked her pocket.")
            elif target == "button":
                self.tell("{hero} found a dull brass button and a polishing cloth in her pocket.",
                          "The button in {hero}'s pocket was tarnished. Beside it was a small cloth.")
            else:
                self.tell("{hero} had the pieces for a brace: a short straight stick and some soft cord. They were not joined yet.",
                          "A small wooden brace could hold the rim up. {hero} had a stick and cord in her pocket, but still had to put them together.")
        elif k == "fetch":
            self.tell("{hero} went home for the {material} and brought it back to the tree.",
                      "She fetched the {material} from home. When she returned, the dragon was still waiting beside the pine.",
                      "There was nothing for it but a trip home. {hero} returned with the {material} safely in her pocket.")
            self.question(event, "Why did {hero} go home?", "The {material} she needed was at home, not in her pocket. She went to get it and brought it back before trying the plan.")
        elif k == "ready_material":
            if target == "button":
                self.tell("The button shone brightly and was small enough to carry.",
                          "It was a bright little button, just the right size for a small beak.")
            else:
                self.tell("The little brace was already assembled, with cord ready to tie its ends in place.",
                          "The brace was small enough for the magpie to carry. Its strong stick and attached cord were ready to use.")
        elif k == "polish":
            self.tell("{hero} rubbed the button with the cloth until the dull brass shone.",
                      "She polished the tarnish from the button. Soon it caught the light like a small, round sun.",
                      "The cloth went round and round the button. {hero} stopped when the brass gleamed.")
            self.dialogue(((("dragon", "You made it worth more."), ("nell", "I made it easier to notice.")),
                           (("dragon", "Is that really treasure?"), ("nell", "Let's let her decide."))), optional=True)
            self.question(event, "How did {hero} improve the button?", "She polished it with a cloth until the brass shone. That made it a brighter ornament for the magpie.")
        elif k == "assemble":
            self.tell("{hero} tied the cord to both ends of the stick, making a little brace that could link the loose rim to a sturdy branch.",
                      "She made a small wooden brace with cord at each end. One end would fasten to the nest's rim and the other to a firm branch.")
            self.dialogue(((("dragon", "That is a rather small piece of engineering."), ("nell", "It is a rather small nest.")),
                           (("dragon", "No jewels in it?"), ("nell", "Just the parts it needs."))), optional=True)
            self.question(event, "How was the brace made?", "{hero} attached soft cord to both ends of a short straight stick. The brace could then be tied between the loose rim and a sturdy branch.")
        elif k == "make_space":
            self.dialogue(((("nell", "Move back, close your mouth, and be quiet."), ("dragon", "All three?"), ("nell", "All three.")),
                           (("nell", "She needs room to come down."), ("dragon", "How much room?"), ("nell", "More than your teeth are giving her."))))
            self.tell("The dragon stepped back, shut his mouth, and fell quiet. The space beneath the nest was clear.",
                      "He moved back from the tree, closed his mouth, and stopped making noise. The magpie could approach without passing his teeth.")
            self.flourish("quiet", ("The space below the nest was quiet now.",) if voice == "plain" else
                          ("For such a large creature, he made a very determined silence.",
                           "Being quiet took up none of the clearing, which was an improvement."))
            self.question(event, "How did the dragon make it safe for the magpie to approach?", "He moved back, closed his mouth, and became quiet. The bird no longer had to pass close to his teeth to reach the offer.")
        elif k == "steady":
            self.dialogue(((("nell", "Can you hold the thick branch from underneath?"), ("dragon", "Without taking the stone?"), ("nell", "For now.")),
                           (("nell", "We need your strength, not your claws inside the nest."), ("dragon", "That is a useful distinction."))))
            self.tell("Keeping his head back, the dragon reached under the thick branch and steadied it with his palm. The nest stopped shifting.",
                      "He supported the thick branch from below, with his mouth still well away. The loose rim rested steadily while they prepared to repair it.")
            self.question(event, "What did the dragon do during the nest repair?", "He steadied the thick branch from underneath while keeping his head back. His temporary support kept the nest still while the permanent brace was fitted.")
        elif k == "offer":
            self.tell("{hero} put the {material} in her tin dish beneath the tree.",
                      "{hero} set the tin dish on the ground and laid the {material} inside it.",
                      "The {material} went into the little tin dish, where the magpie could inspect it.")
            self.dialogue(((("dragon", "Is that all?"), ("nell", "Now she gets to choose.")),
                           (("dragon", "Should I explain its value?"), ("nell", "Let's try letting it be useful."))), optional=True)
        elif k == "take":
            self.tell("The magpie came down, inspected the {material}, and picked it up in her beak.",
                      "Down came the magpie. She examined the {material}, then lifted it from the dish.",
                      "The bird landed beside the dish. After a close look, she took the {material}.")
            self.dialogue(((("dragon", "Well, that's settled."), ("nell", "Not yet. Watch what she does.")),
                           (("dragon", "She likes it."), ("nell", "Yes. Keep waiting."))), optional=True)
        elif k == "carry":
            self.tell("The magpie carried the {material} up to the nest. The {jewel} was still there.",
                      "The bird flew back to the nest with the {material} in her beak. She had not moved the {jewel} yet.")
        elif k == "install_brace":
            self.tell("The magpie fitted the brace between the loose rim and a sturdy branch. She fastened the cord at both ends while the dragon held the branch still.",
                      "With the branch steady, the bird worked the brace into place. Its cord joined the loose rim to a firm branch, giving the nest a new support.")
        elif k == "replace_ornament":
            self.tell("There was room for only one ornament on the little ledge. The magpie put the button there and nudged the {jewel} over the edge.",
                      "The button took the jewel's place on the narrow display ledge. Making room for it, the bird pushed the {jewel} out of the nest.")
            self.tell("Something {color} fell through the branches.", "A {color} speck dropped toward the grass.")
            self.question(event, "Why did the jewel fall from the nest?", "The narrow display ledge had room for only one ornament. The magpie made room for the button by pushing the {jewel} over its edge.")
        elif k == "keep_both":
            self.tell("The ledge was wide enough for both treasures. The magpie set the button beside the {jewel} and kept them both.",
                      "There was a second space on the rim. The magpie put the button in it, leaving the {jewel} exactly where it was.")
            self.dialogue(((("dragon", "She has both of them."), ("nell", "She does."), ("dragon", "That wasn't my plan."), ("nell", "It wasn't an agreement, either.")),
                           (("dragon", "I thought we were swapping."), ("nell", "We put out a present. She accepted a present."))))
            self.question(event, "Why did taking the button not return the jewel?", "The magpie had room to keep both ornaments. Taking the offered button did not by itself mean she had agreed to return the {jewel}.")
        elif k == "request_return":
            self.dialogue(((("nell", "Could you put his stone in the empty dish?"), ("dragon", "She may not understand."), ("nell", "Then I'll show her what I mean.")),
                           (("nell", "Keep the button. Will you bring the other one down?"), ("dragon", "A rather clearer request."))))
            self.tell("{hero} pointed from the {jewel} to the empty dish, then to the dragon. The magpie watched her.",
                      "She showed the bird the empty dish and pointed to the dragon's jewel. Then she stepped aside.")
        elif k == "release":
            if data["use"] == "support":
                self.tell("With the brace fitted, the jewel was no longer holding up the rim. The magpie pulled it free and carried it down to the dish.",
                          "The new brace took the stone's old job. The bird eased the {jewel} out, flew down, and laid it in the tin dish.")
                self.question(event, "Why could the magpie remove the jewel safely?", "The fitted brace had taken over its job of supporting the loose rim. The magpie could pull the stone free and carry it to the dish without letting the nest sag.")
            else:
                self.tell("The magpie left the button on her ledge. She picked up the {jewel}, flew down, and put it in the empty dish.",
                          "This time the bird brought the {jewel} down. She placed it in the dish and went back to her button.")
                self.question(event, "How did the clearer request work?", "{hero} pointed out the jewel and showed the magpie where to put it. The bird then carried it down to the dish, leaving the button in the nest.")
        elif k == "catch":
            self.tell("The dragon caught the {jewel} before it reached the grass. It rested safely in his great claw.",
                      "His claw swept beneath the falling {jewel}. When he opened it, the little stone was safe inside.")
            self.dialogue(((("dragon", "She chose a button."), ("nell", "It was her choice to make.")),
                           (("dragon", "All that trouble for something so small."), ("nell", "You came to my window for something so small."))), optional=True)
        elif k == "collect":
            self.tell("The dragon lifted the {jewel} from the dish and held it safely in his free claw.",
                      "He picked up the returned stone. The {color} jewel lay safely in his free claw.")
        elif k == "withdraw_support":
            self.dialogue(((("nell", "Slowly. See whether the brace holds without you."), ("dragon", "I would prefer not to live under this tree.")),
                           (("dragon", "May I have my other hand back?"), ("nell", "A little at a time."))))
            self.tell("He lowered his supporting hand a little, then took it away. The brace held the rim steady on its own.",
                      "The dragon eased his palm away from the branch. Nothing sagged: the new brace carried the load without him.")
            self.question(event, "How did they know the repair was finished?", "The dragon slowly withdrew his temporary support. The brace held the nest's rim steady without either his hand or the jewel beneath it.")
        elif k == "close":
            outcome = data["outcome"]
            self.tell("They took the path toward {hero}'s house.",
                      "The dragon walked home beside {hero}, leaving the magpie in her tree.",
                      "With the matter settled, they set off along the homeward path.")
            exchanges = {
                "plain": ((("dragon", "How can I thank you?"), ("nell", "Tell me a true story about somewhere you've been."),
                            ("dragon", "I will."), ("nell", "I'll ask questions.")),
                          (("dragon", "What would you like in return?"), ("nell", "A true story from your travels."),
                           ("dragon", "Then I promise you one."), ("nell", "And I'll have questions."))),
                "dry": ((("dragon", "What do I owe you?"), ("nell", "A true story. About somewhere you've been."),
                          ("dragon", "I occasionally make myself look rather magnificent."), ("nell", "I'll ask questions."),
                          ("dragon", "Yes. I rather thought you would. I'll tell you one.")),
                        (("dragon", "May I repay you with a story?"), ("nell", "A true one. From your travels."),
                         ("dragon", "You do make conditions."), ("nell", "And ask questions."), ("dragon", "A true story, then. I promise."))),
                "playful": ((("dragon", "Would you like a treasure?"), ("nell", "A true story from your travels."),
                              ("dragon", "I have some enormous ones."), ("nell", "I have time for questions."), ("dragon", "Then I'll tell you one.")),
                            (("dragon", "I owe you something."), ("nell", "Tell me a true story about a place you've visited."),
                             ("dragon", "May I be splendid in it?"), ("nell", "Only where you really were."), ("dragon", "Agreed. One true story."))),
            }
            self.dialogue(exchanges[voice])
            if outcome == "gift_honored":
                self.tell("Behind them, the {color} jewel stayed in the nest. The dragon's empty claw hung easily beside {hero}.",
                          "The {jewel} was still in the magpie's home. The dragon walked away with an empty claw and a story to tell.")
            elif outcome == "cooperative_repair":
                self.tell("The new brace held firm behind them. The dragon carried his tiny {jewel}, with neither hand left holding up a tree.",
                          "The repaired rim stayed level as they left. The dragon's {jewel} rested in his claw, and his other hand was free.")
            else:
                self.tell("The button shone in the nest. The {jewel} rested in the dragon's claw, and {hero} was already choosing her first question.",
                          "Two small things had found their places: the button in the nest, the {jewel} in his claw. {hero} walked beside him, ready to listen.")
            self.question(event, "What did the dragon promise in return for the help?", "He promised {hero} a true story about his travels. She said she would ask questions; the telling was still ahead of them.")
        else:
            raise StoryError(f"No faithful rendering for event {k!r}.")


ASP_RULES = """
valid(U,O) :- use(U), owner(O).
can_detach(display,dragon,B,T) :- replacement(B), temporary(T).
can_detach(support,dragon,1,T) :- temporary(T).
can_detach(support,dragon,B,1) :- replacement(B).
can_leave(U,bird) :- use(U).
#show valid/2.
#show can_detach/4.
#show can_leave/2.
"""


def valid_combos():
    return list(itertools.product(USES, OWNERS))


def asp_facts():
    from asp import fact
    return "\n".join([fact("use", use) for use in USES] + [fact("owner", owner) for owner in OWNERS]
                     + [fact(name, value) for name in ("replacement", "temporary") for value in (0, 1)])


def asp_combos():
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def generate(p: StoryParams) -> StorySample:
    world = simulate(p)
    rendering = Teller(world.history, p).run()
    return StorySample(params=p, story=rendering.story,
                       prompts=["Write a dialogue-rich story about {hero} helping a dragon understand a magpie and a missing {jewel}.".format(hero=p.hero, jewel=p.jewel)],
                       story_qa=rendering.qa, world_qa=[], world=world)


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about world cases.")
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    expected = set()
    for use, owner, permanent, temporary in itertools.product(USES, OWNERS, (0, 1), (0, 1)):
        w = build_world(StoryParams(use=use, owner=owner))
        if permanent:
            w.relations.add(("brace", "supports", "nest"))
        if temporary:
            w.relations.add(("dragon", "supports", "nest"))
        if can_detach(w):
            expected.add((use, owner, permanent, temporary))
    if set(atoms(model, "can_detach")) != expected or set(atoms(model, "can_leave")) != {(use, "bird") for use in USES}:
        raise StoryError("Python and ASP disagree about release/ownership constraints.")
    count = 0
    for use, owner, supplies, temper, slots in itertools.product(USES, OWNERS, SUPPLIES, TEMPERS, (1, 2)):
        p = StoryParams(use=use, owner=owner, supplies=supplies, temper=temper, nest_slots=slots)
        sample = generate(p)
        signature = trace_signature(sample.world)
        for voice in VOICES:
            other = replace(p, prose_seed=99, voice=voice, flourish_budget=0, detail_level="compact")
            if trace_signature(simulate(other)) != signature:
                raise StoryError("Prose settings changed the simulated events.")
            Teller(sample.world.history, other).run()
        count += 1
    print(f"OK: {count} world configurations; independent renderings; ASP parity.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", "--world-seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    for name, choices in (("hero", NAMES), ("jewel", tuple(JEWELS)), ("use", USES), ("owner", OWNERS),
                          ("supplies", SUPPLIES), ("temper", TEMPERS)):
        parser.add_argument("--" + name, choices=choices)
    parser.add_argument("--nest-slots", type=int, choices=(1, 2))
    parser.add_argument("--voice", choices=VOICES, default="dry")
    parser.add_argument("--dialogue-level", choices=DIALOGUE_LEVELS, default="conversational")
    parser.add_argument("--detail-level", choices=DETAIL_LEVELS, default="normal")
    parser.add_argument("--flourish-budget", type=int, default=2)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng: random.Random, index=0, *, sample=False):
    p = StoryParams(world_seed=args.world_seed + index, prose_seed=args.prose_seed + index,
                    voice=args.voice, dialogue_level=args.dialogue_level,
                    detail_level=args.detail_level, flourish_budget=args.flourish_budget)
    registries = dict(hero=NAMES, jewel=tuple(JEWELS), use=USES, owner=OWNERS,
                      supplies=SUPPLIES, temper=TEMPERS, nest_slots=(1, 2))
    for name, choices in registries.items():
        value = getattr(args, name)
        setattr(p, name, value if value is not None else rng.choice(choices) if sample else getattr(p, name))
    validate_params(p)
    return p


def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(dict(state=sample.world.snapshot(), history=[asdict(e) for e in sample.world.history],
                              trace_sha256=trace_signature(sample.world), causal_sha256=trace_signature(sample.world, causal=True)), indent=2))


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0
        rng = random.Random(args.world_seed)
        if args.all:
            params = []
            for use, owner, slots in itertools.product(USES, OWNERS, (1, 2)):
                if any(getattr(args, key) is not None and getattr(args, key) != value
                       for key, value in dict(use=use, owner=owner, nest_slots=slots).items()):
                    continue
                p = resolve_params(args, rng)
                params.append(replace(p, use=use, owner=owner, nest_slots=slots))
        else:
            params = [resolve_params(args, rng, index, sample=args.n > 1) for index in range(args.n)]
        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for index, p in enumerate(params):
                emit(generate(p), trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(params) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())

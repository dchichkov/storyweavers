#!/usr/bin/env python3
"""Diverse rhyming StoryWorld about evidence, an archer, and reconciliation."""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402

ARCHER_NAMES = ["Arin", "Milo", "Nia", "Tess", "Rook", "Lina", "Pip", "Sera"]
COLONY_NAMES = ["the Clover Colony", "the Moss Colony", "the Pebble Colony"]
PLACES = ["the meadow edge", "the little stone arch", "the apple lane"]
THRESHOLD = 1.0


@dataclass(frozen=True)
class Incident:
    id: str
    residents: str
    event: str
    sign: str
    accusation: str
    cause: str
    harm: str
    clue: str
    mistake: str
    colony_action: str
    archer_action: str
    repair: str
    lesson: str
    image: str
    rhyme: str


INCIDENTS = (
    Incident("bridge", "field mice", "lantern supper", "snapped reeds beside their footbridge", "the mice pulled it apart to block the range path", "a night gust loosened an old knot", "berry baskets could not cross the brook", "windblown leaves lay beneath every broken reed", "tied one knot so tightly that another reed split", "showed which green reeds would bend", "used a bowstring measure to space the lashings", "a flexible new footbridge", "evidence should come before blame", "berry lanterns crossing the bridge in a glowing line", "Whish, swish, reeds in a dish"),
    Incident("ribbons", "bumblebees", "clover festival", "three range ribbons missing from their posts", "the bees took them for streamers", "a magpie wove them into an empty nest", "the closed-range boundary was hard to see", "silver-black feathers dotted the posts", "followed a poppy petal instead of the ribbon trail", "traced the magpie's zigzag flight", "closed the range and fetched the adult steward", "checked boundary ribbons and a safe nest lining", "a clue is stronger than a quick guess", "red ribbons fluttering above bees dancing over clover", "Flip, flap, follow the map"),
    Incident("target", "ladybirds", "dew parade", "tiny red dots across the practice target", "the ladybirds painted it without asking", "dew carried berry dye from a leaking banner", "the scoring rings could not be read", "each red trail began beneath the dripping banner", "wiped wet dye and spread it farther", "placed broad leaves beneath the drips", "waited for the board to dry and helped repaint it", "a crisp target below a mended banner", "patterns reveal causes when tempers cannot", "dew pearls shining beside five clean target rings", "Drop, plop, pause the mop"),
    Incident("markers", "mole crickets", "music hour", "range markers leaning into soft mounds", "the crickets tunneled up to spoil practice", "a leaking garden pipe washed soil away", "the safety boundary was no longer straight", "clear water bubbled where no tunnel opened", "pressed one marker down and watched it lean again", "located the hiss by listening through soil", "kept everyone away and called the caretaker", "a sealed pipe and freshly measured markers", "repeating a failed fix is not investigating", "straight white markers gleaming as cricket music rose", "Drip, thrum, hear where it comes from"),
    Incident("seeds", "harvest ants", "winter seed count", "sunflower seeds scattered across the closed range", "the ants ignored signs to store food there", "a wheelbarrow sack tore on the garden path", "their food trail crossed an unsafe area", "the seeds led to a frayed burlap corner", "swept from the wrong end and scattered the trail", "formed a safe route beyond the target field", "posted a closure and carried the sack to the gardener", "a sheltered seed tray beside their usual path", "safety and sharing improve through planning", "ants circling a golden tray beyond the quiet gate", "Scritch, scratch, mend the patch"),
    Incident("clicks", "click beetles", "moonrise concert", "sharp clicks after the practice bell", "the beetles mocked every careful shot", "seed pods tapped the hollow target stand", "the accusation silenced their concert", "the clicks continued when every beetle was still", "asked for silence twice before listening nearby", "matched the odd clicks to each gust", "racked the bow and padded the seed pods", "a quiet stand and restored concert", "listening longer can undo an unfair inference", "beetles clicking a bright rhythm under the moon", "Click, clack, welcome the music back"),
    Incident("vane", "garden snails", "rain-chart meeting", "their weather vane pointing at the target shed", "the snails turned it to claim the shed", "an apple twig pinned the vane sideways", "rain shelters were placed on the wrong side", "a fresh twig scrape crossed the brass hinge", "read the crooked arrow as a message", "shared three nights of contradictory rain notes", "asked before lifting the twig with the steward", "a free vane and correctly placed leaf shelters", "records and respectful questions correct appearances", "silver snail trails curling toward dry shelters", "Slow, glow, now the true winds show"),
    Incident("bell", "tree frogs", "pond chorus", "the range-closing bell gone from its hook", "the frogs borrowed it for their chorus", "the rusty hook broke and dropped it in grass", "practice could not close with its usual signal", "a rust-colored crescent marked the empty hook", "searched beside the pond instead of below the hook", "sang a rhythm for a grass-by-grass search", "left the bow behind and found the fallen bell", "a brass hook holding the polished bell", "where a thing fell matters more than who lives nearby", "the bell reflecting frogs on moonlit lily pads", "Ding, sing, moonlight on everything"),
    Incident("clock", "honeybees", "blossom-time council", "the colony sun clock dark at noon", "the bees moved range screens to claim shade", "the archer's target cloth slipped over the clock", "foragers returned at mismatched times", "blue target chalk marked the cloth's fold", "studied clouds before noticing the square shadow", "compared the clock with open daisies", "admitted the cloth was theirs and secured it", "a clear clock and firm storage hooks", "reconciliation begins by owning one's part", "bees arriving as noon crossed the clock", "Hum, sun, back on time when work is done"),
    Incident("cup", "woodlice", "damp-leaf picnic", "the shared water cup empty by a wet trail", "the woodlice drained it for their picnic", "a hairline crack leaked under the bench", "the colony was blamed and nobody had water", "the trail began at the cup and stopped early", "filled the cup again without checking its base", "rolled a dry leaf under it to reveal the leak", "labeled it broken and brought clean water", "two filled cups on a stable shaded shelf", "testing simple explanations prevents hurtful claims", "water beads brightening moss around the shelf", "Sip, drip, check the little chip"),
    Incident("windsock", "silkworm moths", "first-flight celebration", "the wind sock wrapped in pale thread", "the moths tangled it to stop practice", "festival bunting unraveled around a branch", "the archer lost a wind guide and moths lost a banner", "one blue thread joined sock and torn bunting", "tugged an end until the knot tightened", "mapped which loops must be freed first", "kept the bow racked and helped the steward", "a free wind sock and firmly tied banner", "shared trouble calls for shared facts", "new wings and the wind sock opening in one breeze", "Twirl, unfurl, let the safe wind curl"),
    Incident("scorecard", "pond skaters", "ripple exhibition", "mud prints across the scorecard", "the skaters spoiled it after the applause", "a robin hopped from a puddle to the bench", "an unfair complaint embarrassed the colony", "three-toed prints dwarfed a skater's feet", "counted stains instead of comparing shapes", "showed their pinprick tracks on a lily leaf", "withdrew the claim and copied the steward's record", "a dry scorecard under a clear cover", "new evidence makes changing one's mind brave", "a robin bathing while skaters drew water rings", "Plot, spot, compare what each foot has got"),
)

OPENINGS = ("Morning unrolled like a ribbon of gold", "Just after breakfast, while cool shadows curled", "On a breezy day bright with song", "Before the colony gathering began", "When noon made clover shadows short", "At the hush between two birdsongs", "As evening polished the path amber", "While the steward checked every safety sign", "Beneath clouds shaped like silver ships", "As the meadow woke one dewdrop at a time")
INFERENCES = ('"I can infer what happened," {n} declared, mistaking suspicion for fact.', '{n} frowned. "From this one sign, I infer the colony caused it."', 'Without asking, {n} made a hurried inference and blamed the colony.', '"The answer looks plain," said {n}, though only one clue was known.', '{n} let one clue grow into a whole conclusion about the colony.', 'A quick thought flashed through {n}: "I infer this was the colony."', '{n} skipped the questions and reached an unfair inference.', 'Instead of testing the idea, {n} announced, "This points to the colony."')
APOLOGIES = ('"I spoke before I knew," {n} said. "I am sorry. May I help repair the harm?"', '"My guess became an accusation," admitted {n}. "That was unfair."', '"You deserved a question, not blame," {n} said. "Let me make this right."', '{n} lowered their voice. "I inferred too much from too little. I apologize."', '"The evidence changed my mind," said {n}. "I was wrong to accuse you."', '{n} faced the colony. "My words hurt. I am sorry, and I will help."', '"A rhyme is not enough for repair," {n} said. "First comes an apology."', '{n} took responsibility: "I blamed you without proof. That was my mistake."')
BRIDGES = ("They compared what each had seen.", "They listened twice and ordered every clue.", "A fair test turned argument into a question.", "Once both sides spoke, the missing piece appeared.", "Observation replaced assumption.", "They checked place, timing, and trail.", "One careful question opened a path blame had closed.", "Together they noticed what neither knew alone.")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    colony_name: str
    archer_name: str
    colony_name2: str
    incident_id: str = "bridge"
    opening_id: int = 0
    inference_id: int = 0
    apology_id: int = 0
    bridge_id: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return copy.deepcopy(self)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming StoryWorld: infer, archer, colony, reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--archer-name", choices=ARCHER_NAMES)
    ap.add_argument("--colony-name", choices=COLONY_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true", dest=flag.replace("-", "_"))
    return ap


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact(a, b) for a, b in (("setting", "meadow"), ("feature", "reconciliation"), ("feature", "rhyming_story"), ("topic", "archer"), ("topic", "colony"), ("topic", "infer"), ("safety", "closed_range")))


ASP_RULES = "valid_story :- setting(meadow), feature(reconciliation), feature(rhyming_story), topic(archer), topic(colony), topic(infer), safety(closed_range).\n#show valid_story/0."


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    ok = any(s.name == "valid_story" for s in asp.one_model(asp_program("#show valid_story/0.")))
    print("OK: ASP gate accepted the safe reconciliation story." if ok else "Mismatch: ASP gate rejected the story.")
    return 0 if ok else 1


def incident_for(key: str) -> Incident:
    try:
        return next(x for x in INCIDENTS if x.id == key)
    except StopIteration as exc:
        raise StoryError(f"Unknown incident: {key}") from exc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    colony_name = args.colony_name or rng.choice(COLONY_NAMES)
    return StoryParams(place=args.place or rng.choice(PLACES), colony_name=colony_name, archer_name=args.archer_name or rng.choice(ARCHER_NAMES), colony_name2=colony_name, incident_id=rng.choice(INCIDENTS).id, opening_id=rng.randrange(len(OPENINGS)), inference_id=rng.randrange(len(INFERENCES)), apology_id=rng.randrange(len(APOLOGIES)), bridge_id=rng.randrange(len(BRIDGES)))


def tell(params: StoryParams) -> World:
    x = incident_for(params.incident_id)
    w = World(params.place)
    a = w.add(Entity(id="archer", kind="character", type="child", label=params.archer_name, role="archer"))
    c = w.add(Entity(id="colony", kind="group", type="animal_colony", label=params.colony_name, role=x.residents, plural=True))
    w.add(Entity(id="target", type="practice_target", label="straw practice target", role="range equipment"))
    w.facts.update(archer=a, colony=c, incident=x, cause=x.cause, repair=x.repair, lesson=x.lesson, resolved=False, range_status="closed")
    w.say(f"{OPENINGS[params.opening_id]}, {a.label} came to {params.place} for supervised archery practice.")
    w.say(f"Beyond the safety rope lived {c.label}, a literal colony of {x.residents} preparing a {x.event}.")
    w.say("The steward checked the empty field; every soft practice arrow stayed safely in its case.")
    w.para()
    w.say(f"Then {a.label} noticed {x.sign}.")
    w.say(INFERENCES[params.inference_id].format(n=a.label))
    w.say(f"They claimed that {x.accusation}. The accusation interrupted the {x.event}, and {x.harm}.")
    w.say(f"The {x.residents} replied, 'Ask what we know before saying it is so.'")
    c.memes.update(hurt=1.0, caution=1.0)
    w.para()
    w.say(f"At first, {a.label} {x.mistake}. {BRIDGES[params.bridge_id]}")
    w.say(f"The decisive clue was that {x.clue}. Together they inferred the real cause: {x.cause}.")
    w.say(f"The colony {x.colony_action}; {a.label} {x.archer_action}.")
    w.say(f"'{x.rhyme},' they rhymed, keeping time with each careful step.")
    w.para()
    w.say(APOLOGIES[params.apology_id].format(n=a.label))
    w.say(f"Together they completed {x.repair}, mending the practical harm as well as the words.")
    w.say("The colony accepted the apology after seeing the repair, and reconciliation replaced the quarrel with a plan.")
    w.say("Their new refrain was, 'Look, ask, test; patient neighbors infer best.'")
    w.say(f"They learned that {x.lesson}.")
    w.say(f"After the steward safely reopened the range, the closing picture was {x.image}.")
    c.memes.update(hurt=0.0, trust=1.0, harmony=1.0)
    a.memes.update(humility=1.0, care=1.0)
    w.facts.update(clue=x.clue, archer_action=x.archer_action, colony_action=x.colony_action, image=x.image, resolved=True, range_status="reopened by the steward")
    return w


def generation_prompts(w: World) -> list[str]:
    f, x = w.facts, w.facts["incident"]
    return [f"Write a child-safe rhyming story in which {f['archer'].label}, an archer, must infer why {x.sign} near {f['colony'].label}.", f"Tell a reconciliation tale about {x.residents} and an archer who learns that {x.lesson}.", f"Use infer, archer, colony, and reconciliation in a story ending with {x.image}."]


def story_qa(w: World) -> list[QAItem]:
    f, x, name = w.facts, w.facts["incident"], w.facts["archer"].label
    return [QAItem(question=f"What led {name} to make an unfair inference?", answer=f"{name} noticed {x.sign} and guessed that {x.accusation}. The guess came before a careful test."), QAItem(question="Which clue revealed the actual cause?", answer=f"The decisive clue was that {x.clue}. It showed that {x.cause}."), QAItem(question="How did the colony help?", answer=f"The {x.residents} {x.colony_action}. Their knowledge replaced blame with evidence."), QAItem(question=f"What did {name} do to make amends?", answer=f"{name} apologized and {x.archer_action}. Together they completed {x.repair}."), QAItem(question="What image proves reconciliation lasted?", answer=f"The story closes with {x.image}. That shared scene shows trust returned after repair.")]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [QAItem(question="What does it mean to infer?", answer="To infer is to reach a conclusion from evidence. A responsible inference changes when new evidence appears."), QAItem(question="What is a biological colony?", answer="It is a group of organisms of the same kind living closely together. Here, colony refers only to small animals."), QAItem(question="What does reconciliation require?", answer="It requires listening, responsibility, and repair after conflict. Actions make an apology meaningful."), QAItem(question="How is archery kept safe here?", answer="Soft arrows are used only on a supervised marked range. The range closes whenever anyone is nearby and reopens only after the steward checks it.")]


def generate(params: StoryParams) -> StorySample:
    w = tell(params)
    return StorySample(params=params, story=w.render(), prompts=generation_prompts(w), story_qa=story_qa(w), world_qa=world_knowledge_qa(w), world=w)


def format_qa(s: StorySample) -> str:
    lines = ["== (1) Generation prompts =="] + [f"{i}. {p}" for i, p in enumerate(s.prompts, 1)] + ["", "== (2) Story questions =="]
    for q in s.story_qa: lines += [f"Q: {q.question}", f"A: {q.answer}"]
    lines += ["", "== (3) World questions =="]
    for q in s.world_qa: lines += [f"Q: {q.question}", f"A: {q.answer}"]
    return "\n".join(lines)


def dump_trace(w: World) -> str:
    return "\n".join(["--- world model state ---"] + [f"  {e.id}: {e.type} {e.label} role={e.role} memes={e.memes}" for e in w.entities.values()] + [f"  fact.{k}={w.facts.get(k)}" for k in ("cause", "clue", "repair", "lesson", "range_status", "image", "resolved")])


def emit(s: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header: print(header)
    print(s.story)
    if trace and s.world: print(dump_trace(s.world))
    if qa: print("\n" + format_qa(s))


CURATED = [
    StoryParams(place="the meadow edge", colony_name="the Clover Colony", archer_name="Arin", colony_name2="the Clover Colony", incident_id="bridge", opening_id=0, inference_id=0, apology_id=0, bridge_id=0),
    StoryParams(place="the little stone arch", colony_name="the Moss Colony", archer_name="Milo", colony_name2="the Moss Colony", incident_id="clicks", opening_id=3, inference_id=4, apology_id=2, bridge_id=5),
    StoryParams(place="the apple lane", colony_name="the Pebble Colony", archer_name="Nia", colony_name2="the Pebble Colony", incident_id="windsock", opening_id=7, inference_id=6, apology_id=7, bridge_id=7),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp: print(asp_program("#show valid_story/0.")); return
    if args.verify: raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print("compatible story:")
        for symbol in asp.one_model(asp_program("#show valid_story/0.")): print(symbol)
        return
    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples, seen, attempt = [], set(), 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            seed, attempt = base + attempt, attempt + 1
            p = resolve_params(args, random.Random(seed)); p.seed = seed
            sample = generate(p)
            if sample.story in seen: continue
            seen.add(sample.story); samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)); return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1: print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

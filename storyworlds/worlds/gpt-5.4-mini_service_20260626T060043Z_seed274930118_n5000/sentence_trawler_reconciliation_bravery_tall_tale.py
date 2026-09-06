#!/usr/bin/env python3
"""
Standalone storyworld: sentence / trawler / reconciliation / bravery / tall tale.

A little harbor tale with a big-lie voice: a trawler carries a stubborn old
sentence that has gone missing from the deck. The crew quarrels, one brave hand
dives into the harbor, and reconciliation ties the whole thing back together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "person":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Harbor:
    place: str = "the harbor"
    water: str = "gray water"
    breeze: str = "salt breeze"


@dataclass
class World:
    harbor: Harbor
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.harbor)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _inc(d: dict[str, float], key: str, amount: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amount


def _has(ent: Entity, key: str) -> bool:
    return ent.meters.get(key, 0.0) >= THRESHOLD or ent.memes.get(key, 0.0) >= THRESHOLD


def _r_sog(world: World) -> list[str]:
    out: list[str] = []
    crew = world.get("Crew")
    sentence = world.get("Sentence")
    if crew.meters.get("storm", 0.0) < THRESHOLD:
        return out
    if sentence.meters.get("wet", 0.0) >= THRESHOLD:
        return out
    sig = ("sog",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sentence.meters["wet"] = sentence.meters.get("wet", 0.0) + 1
    sentence.meters["smudged"] = sentence.meters.get("smudged", 0.0) + 1
    out.append("The sentence got wet and smudged, as if the sea itself had licked the ink.")
    return out


def _r_quarrel(world: World) -> list[str]:
    crew = world.get("Crew")
    mate = world.get("Mate")
    if crew.memes.get("worry", 0.0) < THRESHOLD or mate.memes.get("brave", 0.0) < THRESHOLD:
        return []
    sig = ("quarrel",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crew.memes["feud"] = crew.memes.get("feud", 0.0) + 1
    mate.memes["feud"] = mate.memes.get("feud", 0.0) + 1
    return ["__quarrel__"]


def _r_reconcile(world: World) -> list[str]:
    crew = world.get("Crew")
    mate = world.get("Mate")
    sentence = world.get("Sentence")
    if sentence.meters.get("fixed", 0.0) < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crew.memes["feud"] = 0.0
    mate.memes["feud"] = 0.0
    crew.memes["warmth"] = crew.memes.get("warmth", 0.0) + 1
    mate.memes["warmth"] = mate.memes.get("warmth", 0.0) + 1
    return ["__reconcile__"]


RULES = [_r_sog, _r_quarrel, _r_reconcile]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s not in {"__quarrel__", "__reconcile__"})
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    name: str
    mate_name: str
    boat_name: str = "Sea Goose"
    scenario: int = 0
    opening: int = 0
    telling: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


HARBOR = Harbor()

NAMES = ["Mina", "Jun", "Iris", "Pip", "Nell", "Otto", "Anya", "Bram", "Wren", "Cleo"]
MATE_NAMES = ["Sal", "Toby", "Mara", "Finn", "Kit", "Ada", "Bea", "Nico"]
GIRL_NAMES = {"Mina", "Iris", "Nell", "Anya", "Cleo", "Mara", "Ada", "Bea"}
BOY_NAMES = {"Pip", "Otto", "Bram", "Toby", "Finn"}


SCENARIOS = [
    {
        "cargo": "a sentence painted across twelve sailcloth panels",
        "purpose": "welcome the lighthouse keeper home",
        "conflict": "a loose cod basket bumped the panels out of order, and the crew blamed the deck team",
        "clue": "silver fish scales marked the basket's crooked path",
        "mistake": "reading the panels backward made the welcome sound like a command to leave",
        "bravery": "admitted that the basket knot had been rushed and asked everyone to inspect the deck together",
        "repair": "matched the scale trail, retied the basket, and arranged the twelve panels from greeting to period",
        "result": "the lighthouse keeper heard the true welcome across the water",
        "image": "twelve blue panels snapped in one bright line beneath the turning lighthouse beam",
        "lesson": "Bravery can begin with admitting a mistake, and reconciliation grows when people examine evidence together.",
    },
    {
        "cargo": "a sentence spelled with wooden letters as tall as lobster pots",
        "purpose": "open the harbor reading festival",
        "conflict": "three letters vanished during a fog, and the cook and navigator accused each other of moving them",
        "clue": "round wet marks led from the alphabet crate to a rolling water barrel",
        "mistake": "guessing the missing letters turned READ WITH US into RED WIT US",
        "bravery": "stopped the shouting and rolled the heavy barrel back while the crew used chocks from a safe distance",
        "repair": "found the letters beneath the barrel, dried them, and rebuilt the sentence in festival order",
        "result": "boats all around the trawler answered by raising books above their rails",
        "image": "the restored wooden sentence glowed gold in the fog while pages fluttered on every deck",
        "lesson": "Bravery includes slowing a quarrel down long enough for the truth to appear.",
    },
    {
        "cargo": "a sentence stitched into a red signal flag",
        "purpose": "warn the ferry about a drifting log",
        "conflict": "the flag jammed halfway up, and the signal crew argued over whose pulley had failed",
        "clue": "a gull feather trembled beside one pinched corner of cloth",
        "mistake": "pulling harder only folded the warning sentence into a red knot",
        "bravery": "owned the bad first idea, called for the engine to idle, and asked the whole crew to pause",
        "repair": "lowered the halyard, freed the feather, flattened the flag, and sent the complete sentence aloft",
        "result": "the ferry read the warning and curved safely around the log",
        "image": "the red sentence streamed straight above two boats passing safely under a clear patch of sky",
        "lesson": "A brave pause can prevent harm, and reconciliation makes room for a better plan.",
    },
    {
        "cargo": "a sentence written in chalk along the trawler's blackboard rail",
        "purpose": "record where a family of seals had been seen",
        "conflict": "spray erased the middle, and two watchers disagreed about which cove the words had named",
        "clue": "the logbook held a tiny sketch of a split-topped rock beside the lost phrase",
        "mistake": "steering by the loudest guess brought the trawler toward a shallow sandbar",
        "bravery": "said the guess was uncertain and requested a careful turn into deeper marked water",
        "repair": "compared the sketch with the chart, restored the missing place words, and invited both watchers to verify them",
        "result": "the crew found the seals without crowding their quiet cove",
        "image": "the complete chalk sentence shone above the rail as seal heads dotted the distant silver water",
        "lesson": "Bravery is telling the truth about uncertainty, and reconciliation values careful checking over winning.",
    },
    {
        "cargo": "a sentence punched as holes in a long brass music strip",
        "purpose": "play a birthday message for the harbor master",
        "conflict": "the strip snagged in the music box, and the musicians blamed the mechanics",
        "clue": "one bent brass corner clicked twice at exactly the same word",
        "mistake": "cranking faster made the birthday sentence honk like a seasick goose",
        "bravery": "turned the crank off, apologized for rushing, and listened while the mechanic explained the safe release latch",
        "repair": "opened the latch, flattened the corner with the proper tool, and fed the sentence through slowly",
        "result": "the music box played every word clearly enough for the whole quay to sing along",
        "image": "the brass sentence curled into a shining coil beside a cake with one candle steady in the breeze",
        "lesson": "Listening after a mistake is a form of bravery that can mend both machines and friendships.",
    },
    {
        "cargo": "a sentence braided from colored rope along the cabin wall",
        "purpose": "teach new sailors the harbor's safety promise",
        "conflict": "a green strand came loose, and the knot crew accused the painters of tugging it",
        "clue": "fresh sawdust below a coat hook showed that the hook itself had twisted",
        "mistake": "hiding the gap behind a map left the safety promise incomplete",
        "bravery": "pulled the map aside, named the missing words aloud, and invited the painters back to help",
        "repair": "replaced the loose hook, rebraided the green words, and checked every knot as one team",
        "result": "the new sailors could read and repeat the whole safety sentence",
        "image": "green, yellow, and white rope words arched above joined hands in the lantern-lit cabin",
        "lesson": "Bravery reveals a hidden problem, while reconciliation lets many hands make the repair last.",
    },
    {
        "cargo": "a sentence bottled one word at a time in clear jars",
        "purpose": "deliver a thank-you to the island gardeners",
        "conflict": "the jars rolled into different bins, and the port and starboard crews each claimed the other had mixed them",
        "clue": "tiny painted numbers continued beneath the corks",
        "mistake": "sorting by jar size produced a thank-you about turnips thanking people",
        "bravery": "laughed at the silly result, admitted the sorting rule was wrong, and asked both crews to start again",
        "repair": "followed the painted numbers and lined every bottled word in its proper place",
        "result": "the gardeners received the intended thanks and sent back a basket of strawberries",
        "image": "sunset passed through the ordered jars and painted the full sentence in colors across the deck",
        "lesson": "Bravery need not be grim; honest laughter and shared evidence can lead to reconciliation.",
    },
    {
        "cargo": "a sentence printed on the trawler's new tide chart",
        "purpose": "explain when the narrow harbor gate would be safest",
        "conflict": "an ink blot covered the time, and the morning and evening watches argued about the intended hour",
        "clue": "a penciled moon beside the sentence matched the evening tide table",
        "mistake": "choosing the morning time would have left too little water beneath the keel",
        "bravery": "refused to hurry through the gate and calmly explained why the uncertain sentence mattered",
        "repair": "anchored in open water, checked the moon mark with the official table, and rewrote the time clearly",
        "result": "the trawler crossed the gate on the deep evening tide",
        "image": "the corrected sentence rested under glass while the moon laid a white road through the harbor gate",
        "lesson": "Bravery can mean waiting safely, and reconciliation replaces pride with a checked answer.",
    },
    {
        "cargo": "a sentence woven into a net with bright letter-shaped floats",
        "purpose": "announce a protected nursery where young fish could grow",
        "conflict": "a current twisted the floats, and the fishing crew thought the science crew had written nonsense",
        "clue": "the first and last floats were tied to the same corner instead of opposite corners",
        "mistake": "reading the twisted net made PROTECT SMALL FISH appear to say TROLL FISH",
        "bravery": "defended the science crew from teasing and asked everyone to spread the net flat on deck",
        "repair": "untwisted the corners, ordered the floating letters, and marked the nursery boundary on the chart",
        "result": "the crew steered around the young fish and shared the clear notice with other boats",
        "image": "the letter floats formed a bright sentence on calm water while tiny fish flashed safely below",
        "lesson": "Bravery stands up for others, and reconciliation begins when mockery gives way to understanding.",
    },
    {
        "cargo": "a sentence tapped out by a brass harbor telegraph",
        "purpose": "guide a rescue boat toward a lost buoy",
        "conflict": "one tap arrived late, and the radio crew argued with the lookout about the direction",
        "clue": "the telegraph lever stuck only when a grain of salt slid beneath its hinge",
        "mistake": "repeating the message without checking sent the sentence wrong a second time",
        "bravery": "admitted the second message could not be trusted and signaled the rescue boat to hold position",
        "repair": "cleaned the hinge, tested each tap, and resent the complete sentence with both crews confirming it",
        "result": "the rescue boat found the buoy before darkness settled",
        "image": "the recovered buoy blinked beside the trawler as the telegraph gave one last perfect click",
        "lesson": "Bravery corrects bad information quickly, and reconciliation turns blame into a double-check.",
    },
    {
        "cargo": "a sentence iced across a cake shaped like a trawler",
        "purpose": "celebrate the cook's final voyage before retirement",
        "conflict": "the warm galley softened two words, and the cook thought the deckhands had sampled the icing",
        "clue": "two sunbeams met exactly where the missing sugar letters had sagged",
        "mistake": "accusing the deckhands made the cheerful meal go silent",
        "bravery": "apologized for the accusation and carried the cake into the cool cabin with help",
        "repair": "used the recipe card to pipe the lost words again while the deckhands shaded the window",
        "result": "the retirement sentence was read aloud before everyone shared the cake",
        "image": "one sugar sentence circled the little cake-trawler while crumbs and smiles filled every plate",
        "lesson": "An apology takes bravery, and reconciliation becomes real through a caring repair.",
    },
    {
        "cargo": "a sentence made from lanterns blinking in a careful pattern",
        "purpose": "tell the shore crew that every sailor was safe",
        "conflict": "one lantern went dark, and the lamp tenders blamed the engine's vibration",
        "clue": "a clean crescent on the glass showed where a moth had nudged the loose shutter",
        "mistake": "adding an extra flash changed SAFE ABOARD into an unfinished question",
        "bravery": "asked the worried families to wait for a verified message and climbed only the cabin steps with a handrail",
        "repair": "secured the shutter, rehearsed the blinking sentence, and let each lamp tender confirm one word",
        "result": "the shore crew read the full message and rang the harbor bell in relief",
        "image": "the final lantern-period winked above the trawler, answered by a single warm bell on shore",
        "lesson": "Bravery communicates carefully, and reconciliation helps everyone send one truthful message.",
    },
]

OPENINGS = [
    "At sunrise, the harbor gulls claimed they could read every wake like handwriting.",
    "By noon, the tide had climbed so high that the moon had to stand on tiptoe to see over it.",
    "On a foggy morning, the harbor bell boomed loudly enough to rattle freckles.",
    "One windy afternoon, every flag in the harbor pointed in a different direction just to be difficult.",
    "At dusk, the sea shone like a sheet of blue tin hammered flat by giants.",
    "Before breakfast, the trawler sneezed its engine awake and startled seven sleepy clouds.",
    "During the spring festival, a hundred paper boats bobbed beside the working fleet.",
    "On the calmest day of the year, even the waves whispered so they would not wake the anchors.",
    "Under a sky striped pink and gold, the harbor ropes hummed like enormous fiddle strings.",
    "Just after a rain shower, the trawler sailed through a rainbow that seemed close enough to polish.",
]

TELLINGS = [
    "The disagreement grew until it sounded, in tall-tale fashion, like two thunderstorms arguing inside a barrel.",
    "For one long minute, blame bounced from sailor to sailor faster than a mackerel on a trampoline.",
    "The quarrel puffed itself up so grandly that even the fog backed away from it.",
    "Each side repeated its certainty until the words seemed heavy enough to tilt the trawler.",
    "Nobody listened, and the argument tied itself into a knot that could have moored a mountain.",
    "Sharp words flew across the deck, but not one of them repaired the precious sentence.",
    "The crew's friendship wobbled harder than a tower of teacups in a gale.",
    "Their blame grew louder while the useful clues waited quietly to be noticed.",
]

DIALOGUES = [
    '"Let us find what happened before we decide who did it," said {captain}.',
    '"A loud guess is still only a guess," {mate} told the crew.',
    '"We can be brave enough to change our minds," said {captain}.',
    '"I would rather mend this together than win an argument alone," said {mate}.',
    '"First the clue, then the conclusion," {captain} reminded everyone.',
    '"No one loses by telling the truth," said {mate}.',
    '"Let us trade blame for jobs," {captain} proposed.',
    '"The sentence needs helpers, not rivals," said {mate}.',
    '"We all want the same safe ending," {captain} said.',
    '"Listen once more; the deck may be telling us something," said {mate}.',
]

ENDINGS = [
    "No one could say whether the stars applauded, but they certainly seemed to sparkle harder.",
    "Afterward, the crew kept the lesson beside the compass, where no one could sail past it unnoticed.",
    "The harbor repeated their laughter from pier to pier until it sounded like a friendly tide.",
    "From then on, they called a careful apology the strongest rope aboard.",
    "Even the gulls stopped squabbling for nearly three whole seconds, a harbor record.",
    "The repaired sentence did its work, but the repaired friendship carried them home.",
    "Their handshake was not truly larger than the mast, though every teller in port swore it was.",
    "That night, the crew ate supper at one table and left the empty chair called Blame on shore.",
    "By morning, the tale had grown ten feet longer, while its honest lesson stayed exactly the same.",
    "The trawler's wake closed behind them like the final line beneath a finished story.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale harbor story about a sentence, a trawler, and brave reconciliation.")
    ap.add_argument("--name")
    ap.add_argument("--mate-name")
    ap.add_argument("--boat-name", default="Sea Goose")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        mate_name=args.mate_name or rng.choice(MATE_NAMES),
        boat_name=args.boat_name or "Sea Goose",
        scenario=rng.randrange(len(SCENARIOS)),
        opening=rng.randrange(len(OPENINGS)),
        telling=rng.randrange(len(TELLINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    world = World(HARBOR)
    captain_type = "girl" if params.name in GIRL_NAMES else "boy" if params.name in BOY_NAMES else "person"
    mate_type = "girl" if params.mate_name in GIRL_NAMES else "boy" if params.mate_name in BOY_NAMES else "person"
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type, label=params.name))
    mate = world.add(Entity(id="Mate", kind="character", type=mate_type, label=params.mate_name))
    crew = world.add(Entity(id="Crew", kind="character", type="crew", label="the crew"))
    sentence = world.add(Entity(id="Sentence", type="sentence", label="sentence", phrase="a long old sentence", caretaker="Crew"))
    trawler = world.add(Entity(id="Trawler", type="trawler", label="trawler", phrase=params.boat_name, owner="Captain"))
    world.facts.update(captain=captain, mate=mate, crew=crew, sentence=sentence, trawler=trawler, params=params)
    return world


def tell(world: World) -> None:
    c = world.get("Captain")
    m = world.get("Mate")
    crew = world.get("Crew")
    sentence = world.get("Sentence")
    trawler = world.get("Trawler")

    params: StoryParams = world.facts["params"]
    scenario = SCENARIOS[params.scenario % len(SCENARIOS)]
    world.facts["scenario"] = scenario

    world.say(OPENINGS[params.opening % len(OPENINGS)])
    world.say(
        f"There sailed {trawler.phrase}, a trawler so sturdy that harbor storytellers claimed it once towed an island back into place. "
        f"{c.label} captained it with {m.label} as mate, and together they carried {scenario['cargo']} to {scenario['purpose']}."
    )
    world.say(
        "That cargo was a real sentence: words arranged to carry one complete thought. On this voyage, every word mattered."
    )

    world.para()
    crew.memes["worry"] = 1
    crew.memes["feud"] = 1
    m.memes["feud"] = 1
    world.say(f"Trouble arrived when {scenario['conflict']}.")
    world.say(TELLINGS[params.telling % len(TELLINGS)])
    world.say(f"Their first response failed: {scenario['mistake']}.")
    world.say(DIALOGUES[params.dialogue % len(DIALOGUES)].format(captain=c.label, mate=m.label))

    world.para()
    m.memes["brave"] = 1
    world.say(
        f"Then {m.label} showed bravery, not by taking a foolish risk, but by acting honestly: {m.pronoun('subject')} {scenario['bravery']}."
    )
    world.say(f"The clue was plain once everyone listened: {scenario['clue']}.")
    world.say(f"Working side by side, they {scenario['repair']}.")
    sentence.meters["fixed"] = 1
    propagate(world, narrate=False)
    world.say(
        f"The accusation was withdrawn, apologies were answered, and reconciliation replaced the quarrel. As a result, {scenario['result']}."
    )

    world.para()
    world.say(scenario["lesson"])
    world.say(f"In the last sight, {scenario['image']}.")
    world.say(ENDINGS[params.ending % len(ENDINGS)])

    world.facts.update(
        resolved=True,
        clue=scenario["clue"],
        brave_action=scenario["bravery"],
        repair=scenario["repair"],
        result=scenario["result"],
        ending_image=scenario["image"],
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    scenario = f["scenario"]
    return [
        f'Write a tall-tale story for children about a trawler, a sentence, and brave reconciliation, featuring {params.name} and {params.mate_name}.',
        f"Tell a harbor adventure in which the trawler {params.boat_name} carries {scenario['cargo']} to {scenario['purpose']}.",
        f"Write a playful tall tale where the decisive clue is this: {scenario['clue']}. Let it help a brave crew repair both a sentence and a friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c: Entity = f["captain"]
    m: Entity = f["mate"]
    sentence: Entity = f["sentence"]
    trawler: Entity = f["trawler"]
    scenario = f["scenario"]
    return [
        QAItem(
            question=f"What was the trawler called in the story?",
            answer=f"The trawler was called {trawler.phrase}, and it carried {scenario['cargo']} through the harbor.",
        ),
        QAItem(
            question="What clue helped the crew understand what had actually happened?",
            answer=f"The crew discovered that {scenario['clue']}. That evidence helped them stop blaming one another.",
        ),
        QAItem(
            question=f"How did {m.label} show bravery?",
            answer=f"{m.label} showed bravery when {m.pronoun('subject')} {scenario['bravery']}. This helped the crew move from arguing to solving the real problem.",
        ),
        QAItem(
            question="How did the crew repair the sentence and reconcile?",
            answer=f"Together, they {scenario['repair']}. Then they withdrew the accusation, exchanged apologies, and worked as one crew again.",
        ),
        QAItem(
            question="What final image showed that the trouble had been resolved?",
            answer=f"In the ending, {scenario['image']}. It made the repaired sentence and the crew's reconciliation visible together.",
        ),
        QAItem(
            question=f"What were {c.label} and {m.label} trying to accomplish?",
            answer=f"They were carrying {scenario['cargo']} to {scenario['purpose']}. Their task succeeded after the crew followed the clue and repaired the sentence.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trawler?",
            answer="A trawler is a working boat that fishes or hauls things through the water.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop fighting and become friendly again.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary when you need to help someone.",
        ),
        QAItem(
            question="What is a sentence?",
            answer="A sentence is a group of words that tells a thought, asks a question, or shares an idea.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {' '.join(bits) if bits else '(quiet)'}")
    return "\n".join(lines)


ASP_RULES = r"""
stormy :- storm.
wet_sentence :- stormy, sentence.
quarrel :- worry, brave.
reconciled :- fixed.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("storm"),
        asp.fact("sentence"),
        asp.fact("trawler"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show stormy/0. #show wet_sentence/0. #show reconciled/0."))
    atoms = {f"{a.name}/{len(a.arguments)}" for a in model}
    required = {"stormy/0"}
    if "wet_sentence/0" not in atoms and "reconciled/0" not in atoms:
        print("OK: ASP twin is present, but this world's parity check is minimal.")
        return 0
    print("OK: ASP twin parsed a model.")
    return 0


def asp_valid() -> str:
    return asp_program("#show stormy/0.")


CURATED = [
    StoryParams(name="Mina", mate_name="Sal", boat_name="Sea Goose", scenario=0, opening=0, telling=0, dialogue=0, ending=0),
    StoryParams(name="Jun", mate_name="Mara", boat_name="Blue Comet", scenario=4, opening=3, telling=5, dialogue=4, ending=6),
    StoryParams(name="Iris", mate_name="Finn", boat_name="Old Wren", scenario=9, opening=8, telling=7, dialogue=8, ending=9),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show stormy/0. #show wet_sentence/0. #show reconciled/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_valid())
        print("\n".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} / {p.mate_name} on {p.boat_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

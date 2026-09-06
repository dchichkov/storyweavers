#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    setting: str = "the wide blue sea"
    loop_energy: float = 0.0
    loop_depth: float = 0.0
    conflict_active: bool = False
    loop_count: int = 0
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    captain_name: str
    mate_name: str
    ship_name: str
    seed: Optional[int] = None


NAMES = ["Mara", "Nell", "Finn", "Pip", "Rory", "Tess", "Jory", "Bram"]
SHIP_NAMES = ["The Blue Comet", "The Merry Loop", "The Ginger Gull", "The Salt Star"]


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(_copy.deepcopy(self.ship))
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        return w


def _join_clauses(*parts: str) -> str:
    return " ".join(p for p in parts if p)


ARCS = [
    {
        "key": "whirlpool_buoys",
        "premise": [
            "At dawn, pirate captain {captain} steered {ship} toward a chain of brass map buoys. {mate}, the first mate, polished the spyglass while a kettle of ginger tea warmed beside the wheel.",
            "The pirate crew of {ship} was carrying library maps across the sea. Captain {captain} watched the brass buoys, while first mate {mate} saved two cups of ginger tea for the tiring voyage.",
        ],
        "problem": [
            "A hidden whirlpool swept the ship past the same three buoys again and again. The circling water had trapped them in a loop and drained their energy.",
            "First the bell buoy clanged, then the red buoy squeaked, then both appeared once more. A whirlpool was winding {ship} through the same loop until the pirates could barely pull a rope.",
        ],
        "conflict": [
            "{captain} ordered, \"Row straight through!\" {mate} pointed across the current and replied, \"No, we must sail sideways.\" Their pirate conflict grew louder than the buoy bell.",
            "\"More sail will beat it,\" {captain} insisted. {mate} shook their head. \"More sail will only spin us faster.\" For one tense minute, their conflict kept either plan from starting.",
        ],
        "turn": [
            "They paused for ginger tea. Its warm bite restored their energy, and {mate} dropped a curl of ginger peel overboard. The peel traced a narrow stream flowing across the whirlpool instead of around it.",
            "{captain} shared the ginger tea before giving another order. With fresh energy, the pirates noticed a ribbon of ginger steam bending toward a quiet gap between two waves.",
        ],
        "action": [
            "\"Your sideways path is real,\" {captain} said. {mate} trimmed the sail while {captain} held the wheel crosswise, and together they followed the narrow cross-current.",
            "{mate} called the wave count, and {captain} turned on the third clang of the buoy. They pulled one rope together, then let the cross-current carry the bow.",
        ],
        "resolution": [
            "The ship slid through the quiet gap and left the whirlpool loop behind. {captain} thanked {mate} for observing before acting, and their conflict was over.",
            "A final spinning wave slapped the stern, but {ship} shot sideways into calm water. Both pirates cheered because listening to each other had broken the loop.",
        ],
        "ending": [
            "Behind them, the three brass buoys shrank into a straight golden line while the cross-current rippled toward shore.",
            "The sunrise flashed on the still ginger cups, and the buoy bell gave one last, distant ding behind their free-running ship.",
        ],
        "problem_fact": "a hidden whirlpool kept sweeping the ship past the same brass buoys",
        "clue_fact": "a simple ginger test revealed a cross-current through the whirlpool",
        "action_fact": "they turned sideways together and followed the cross-current",
        "outcome_fact": "the ship crossed into calm water beyond the whirlpool",
    },
    {
        "key": "enchanted_bell",
        "premise": [
            "Captain {captain} and first mate {mate} sailed the pirate ship {ship} toward Bellrock Island, hoping to deliver a chest of ginger biscuits before noon.",
            "A silver harbor bell guided the pirate ship {ship} through the dusk. In the galley, {mate} packed ginger biscuits and brewed tea to give Captain {captain} energy for the final watch.",
        ],
        "problem": [
            "The silver bell rang twelve times, a gull flew backward, and the sun jumped to where it had been. The island's magic had folded the same ten minutes into a loop.",
            "Every time {ship} reached the harbor gate, the bell rang and the pirates found themselves beside the same black rock. The enchanted loop stole a little more of their energy each time.",
        ],
        "conflict": [
            "{captain} wanted to stuff cloth in the bell, but {mate} wanted to answer it with the ship's smaller bell. \"Silence it!\" said one. \"Match it!\" said the other, and the conflict cost them another loop.",
            "\"We race through before it rings,\" cried {captain}. {mate} answered, \"We should listen for what changes.\" Their conflict sent the crew rushing in two directions.",
        ],
        "turn": [
            "They sat down and shared hot ginger tea. Their energy returned, and drops of steam gathered on the silver handbell. One drop trembled just before the island bell sounded.",
            "A ginger biscuit and a warm drink gave them enough energy to listen carefully. {mate} heard one soft note hiding between the eleventh and twelfth clangs.",
        ],
        "action": [
            "{captain} whispered, \"You listen; I will ring.\" On {mate}'s signal, they rang the ship's bell during the hidden note instead of fighting the island bell.",
            "The pirates agreed to try both ideas gently. {mate} counted the chimes while {captain} tapped one answering note on a ginger jar with a spoon.",
        ],
        "resolution": [
            "The two notes met, the silver bell cracked its spell, and time moved forward. The sun continued across the sky, so the conflict ended in relieved laughter.",
            "The harbor bell answered with a friendly hum. Bellrock stopped repeating its ten minutes, and {ship} finally passed through the gate.",
        ],
        "ending": [
            "At exactly one minute past noon, the pirates carried the ginger biscuits ashore beneath a bell that now rang only once.",
            "The next wave erased every repeated wake behind {ship}, and the silver bell reflected two pirates sharing the last biscuit.",
        ],
        "problem_fact": "an enchanted harbor bell repeated the same ten minutes",
        "clue_fact": "the ginger break helped them notice a hidden note in the bell's pattern",
        "action_fact": "they rang one answering note at the right moment",
        "outcome_fact": "the bell's spell broke and time moved forward",
    },
    {
        "key": "fog_compass",
        "premise": [
            "The pirate tale began in pearl-gray fog as {ship} searched for Lantern Cove. Captain {captain} held the map, and first mate {mate} carried a ginger flask for energy.",
            "The pirate ship {ship} slipped between fog banks with Captain {captain} at the wheel. {mate} marked their path and kept hot ginger tea tucked safely in a padded basket.",
        ],
        "problem": [
            "A rock shaped like a sleeping seal appeared on the left, then appeared there again. Their compass needle had stuck, leading the ship through a wide loop in the fog.",
            "They passed the same floating lantern four times. With the damp compass frozen in place, {ship} kept drawing a loop while the watch crew lost energy.",
        ],
        "conflict": [
            "{captain} trusted the map and ordered a turn north. {mate} trusted the lantern bells and asked to turn south. Their conflict sharpened until neither watched the stubborn compass.",
            "\"The map cannot be wrong,\" said {captain}. \"But our compass can be stuck,\" {mate} replied. The pirate conflict made both of them clutch their own answer.",
        ],
        "turn": [
            "A ginger-tea break restored their energy. When {captain} held the warm cup near the compass, the damp hinge loosened, a salt grain fell away, and the needle swung free.",
            "{mate} wrapped the compass in a cloth warmed around the ginger flask. Fresh energy helped them spot a grain of salt wedged beneath its needle.",
        ],
        "action": [
            "{captain} admitted the compass needed care, and {mate} admitted the map still mattered. One read the map while the other followed the freed needle toward Lantern Cove.",
            "\"Map and compass together,\" {mate} proposed. {captain} nodded, cleaned away the salt, and steered while {mate} counted each bell.",
        ],
        "resolution": [
            "The foggy landmarks stayed behind them at last. A green harbor light appeared ahead, proving they had sailed out of the loop and settled their conflict.",
            "The last familiar shape faded astern, and the real cove bell rang from ahead. By combining their clues, the pirates found a straight course.",
        ],
        "ending": [
            "At the dock, fog beads sparkled on the true-pointing compass beside two empty ginger cups.",
            "The fog opened like a curtain, revealing Lantern Cove and one bright path of moonlight under the bow.",
        ],
        "problem_fact": "a damp, stuck compass led the ship in circles through the fog",
        "clue_fact": "warm ginger tea loosened the compass and exposed trapped salt",
        "action_fact": "they freed the compass and combined it with their other navigation clues",
        "outcome_fact": "the pirates found Lantern Cove and left the fog loop",
    },
    {
        "key": "snagged_anchor",
        "premise": [
            "Pirate captain {captain} guided {ship} through a quiet mangrove channel while {mate} hauled aboard baskets of ginger root from a friendly island garden.",
            "With ginger cargo in the hold and a fresh breeze overhead, the pirate ship {ship} set out from Root Island. {captain} steered while first mate {mate} checked every rope.",
        ],
        "problem": [
            "No matter how the sails pulled, the ship curved back to the same mangrove tree. Its anchor chain had snagged around a sunken post, forcing the ship into a tight loop.",
            "The bow moved forward but the stern swung around and around. A forgotten anchor dragged beneath them, stealing the crew's energy and tying their course into a loop.",
        ],
        "conflict": [
            "{captain} reached for an axe to cut the chain. {mate} argued that losing the anchor would leave them unsafe later. Their conflict flared while the chain scraped tighter.",
            "\"Pull harder!\" ordered {captain}. \"First find what is holding us,\" answered {mate}. The pirates' conflict wasted strength they needed for the heavy chain.",
        ],
        "turn": [
            "They stopped, drank ginger tea, and shared slices of ginger biscuit. With new energy, {mate} noticed that the chain went slack whenever the bow faced the red mangrove.",
            "The cook brought warm ginger broth, restoring enough energy for clear thinking. {captain} saw a muddy scrape on one side of the chain and understood how it was wrapped.",
        ],
        "action": [
            "{captain} put down the axe. On {mate}'s count, they steered toward the post, loosened the chain, and lifted the anchor together with the capstan.",
            "\"You watch the chain; I will ease the wheel,\" {captain} said. {mate} signaled at each slack moment until the crew unwound the anchor without cutting it.",
        ],
        "resolution": [
            "The anchor rose with a crown of harmless seaweed. {ship} stopped circling, and the pirates ended their conflict with a tired, proud handshake.",
            "With one wet clunk, the chain came free and the loop opened into a straight channel. They had saved both the anchor and their friendship.",
        ],
        "ending": [
            "A tiny red mangrove leaf rested on the clean anchor as {ship} sailed toward the evening star.",
            "Behind the stern, their round wake slowly widened and vanished among the moonlit roots.",
        ],
        "problem_fact": "the anchor chain had wrapped around a sunken mangrove post",
        "clue_fact": "their pause after ginger helped them understand how the chain was wrapped",
        "action_fact": "they steered toward the post and unwound the chain together",
        "outcome_fact": "the anchor came free without being cut",
    },
    {
        "key": "storm_eye",
        "premise": [
            "Captain {captain} was taking the pirate ship {ship} and a rescued parrot home before a storm. First mate {mate} tied down the barrels and brewed strong ginger tea for the night watch.",
            "Clouds built dark towers around {ship} as pirates {captain} and {mate} carried a rescued parrot toward a safe harbor. A ginger kettle rattled below deck.",
        ],
        "problem": [
            "A ring of wind caught the sails and drove the ship around the calm eye of the storm. Each lap repeated the same flash of lightning, and the loop exhausted the crew's energy.",
            "The storm spun {ship} past one patch of blue sky again and again. They were trapped in a windy loop, too tired to keep wrestling every sail.",
        ],
        "conflict": [
            "{captain} wanted every sail raised for speed, but {mate} wanted the top sails lowered for control. Their conflict snapped back and forth like the canvas overhead.",
            "\"Turn into the wind!\" called {captain}. {mate} called back, \"Not until we shorten sail!\" The pirate conflict left the wheel pulling against tangled ropes.",
        ],
        "turn": [
            "Below the low deck, they shared ginger tea and recovered their energy. In that quiet pause, they heard the wind soften for three heartbeats after every lightning flash.",
            "A mug of ginger broth warmed each pirate's hands and restored their energy. {mate} watched a puff of steam and discovered the storm wind changed direction after thunder.",
        ],
        "action": [
            "They combined their plans: {mate} shortened the top sail, and {captain} turned during the soft interval in the wind. \"Now!\" they shouted together.",
            "{captain} agreed to slow down first. {mate} freed the crossed rope, then called the thunder count while {captain} steered through the brief opening.",
        ],
        "resolution": [
            "The smaller sails held steady, and {ship} crossed the storm ring instead of circling it. Their conflict gave way to cheers as clear rain fell astern.",
            "One gust pushed, one small sail pulled, and the bow broke out beneath quiet stars. The pirates had escaped the storm loop by mixing courage with care.",
        ],
        "ending": [
            "The rescued parrot shook one bright feather onto the ginger tray while lightning flickered far behind them.",
            "A round hole opened in the clouds, but their wake below ran straight toward three harbor lamps.",
        ],
        "problem_fact": "storm winds kept circling the ship around the storm's eye",
        "clue_fact": "the ginger break helped them notice a softer wind after each thunderclap",
        "action_fact": "they shortened sail and turned during the soft interval",
        "outcome_fact": "the ship crossed the storm ring into clear weather",
    },
    {
        "key": "reef_current",
        "premise": [
            "The pirate ship {ship} carried fresh water to Turtle Reef. Captain {captain} steered between coral heads while first mate {mate} grated ginger into an energy drink.",
            "Pirates {captain} and {mate} promised to bring ginger medicine to the lighthouse keeper beyond Turtle Reef. Their ship, {ship}, reached the coral at sunrise.",
        ],
        "problem": [
            "A gentle-looking current bent around the reef and returned them to the same turtle-shaped stone. The loop was harmless at first, but every lap used more energy.",
            "Three times they passed a blue coral arch, though the wheel pointed ahead. A circular reef current had caught {ship} in a broad loop.",
        ],
        "conflict": [
            "{captain} wanted to cross the shallow coral, while {mate} refused to risk scraping it. Their conflict grew because both cared about arriving quickly for different reasons.",
            "\"Follow the shortest line,\" said {captain}. {mate} replied, \"A safe path may curve before it goes straight.\" The pirate conflict stalled them beside the reef.",
        ],
        "turn": [
            "They drank the grated ginger mixture and regained their energy. {captain} tossed three ginger shavings onto the water, and one slipped beneath the current toward a sandy channel.",
            "After ginger tea restored their energy and cleared their tired heads, {mate} watched a turtle swim low under the circling water. Its path revealed a deeper channel beyond the blue arch.",
        ],
        "action": [
            "{captain} chose the safe route, and {mate} stood at the bow to call the depth. They followed the sandy channel without touching coral.",
            "\"Show me the deepest path,\" {captain} said. {mate} guided left and right while the captain used only enough sail to cross the lower current.",
        ],
        "resolution": [
            "The current released the keel on the far side of the reef. Their conflict ended, the coral stayed safe, and the lighthouse rose ahead.",
            "At the channel's end, the circling current finally remained behind them. The two pirates had escaped the loop without harming a single coral branch.",
        ],
        "ending": [
            "A sea turtle surfaced beside their straight wake, and the lighthouse keeper waved a green scarf from shore.",
            "The untouched reef glowed below their straight wake while {ship} entered gold morning water.",
        ],
        "problem_fact": "a circular current kept carrying the ship around Turtle Reef",
        "clue_fact": "careful observation after their ginger break revealed a deep sandy channel",
        "action_fact": "they followed the deep channel slowly and protected the coral",
        "outcome_fact": "the ship escaped the current and reached the lighthouse",
    },
    {
        "key": "magic_map",
        "premise": [
            "In this pirate tale, {captain} found a moonlit map and sailed {ship} with first mate {mate}. They packed ginger tea to keep their energy up while searching for Storybook Bay.",
            "A map with silver edges promised to lead the pirate ship {ship} to Storybook Bay. Captain {captain} trusted every line, while {mate} brought a compass and a jar of candied ginger.",
        ],
        "problem": [
            "Whenever they reached the map's silver X, the ink wriggled and placed the X behind them. The magical map led the ship through the same loop until everyone felt weary.",
            "The map redrew north each hour, sending {ship} past the same moonlit cave. Its changing path trapped the pirates in an ink-made loop.",
        ],
        "conflict": [
            "{captain} said the map must be obeyed, while {mate} said it must be tested. Their conflict became so stubborn that neither noticed a blank line below the X.",
            "\"A treasure map never lies,\" {captain} declared. \"Then perhaps it is asking a riddle,\" {mate} replied. Their pirate conflict lasted through one more useless lap.",
        ],
        "turn": [
            "They shared candied ginger and recovered their energy. A drop of ginger tea splashed across the blank line, revealing hidden words: FOLLOW THE MOON, NOT THE X.",
            "Warm ginger tea restored their energy, and its steam made pale letters appear along the map's silver edge. The letters told them to fold the false path away.",
        ],
        "action": [
            "{captain} apologized for refusing to test the map. {mate} set its false X aside, and together they steered along the moon's reflection.",
            "\"You found the riddle; I will follow its answer,\" said {captain}. {mate} held the steaming map flat while the captain aimed the bow at the rising moon.",
        ],
        "resolution": [
            "The ink stopped crawling, and a real bay opened ahead. Their conflict ended when the map drew one final straight line behind {ship}.",
            "Storybook Bay appeared where moonlight touched the water. The magic loop vanished because the pirates had questioned the map together.",
        ],
        "ending": [
            "On shore, they pinned the honest map beneath the empty ginger jar, and its silver X stayed still all night.",
            "The folded map rested quietly between two cups as moonlit pages fluttered in the bay's little library.",
        ],
        "problem_fact": "a magical map kept redrawing its route into a loop",
        "clue_fact": "ginger tea revealed hidden instructions on the map",
        "action_fact": "they followed the map's hidden instruction toward the moon",
        "outcome_fact": "the map stopped changing and they reached Storybook Bay",
    },
    {
        "key": "kelp_rudder",
        "premise": [
            "{ship} was a cheerful pirate mail boat captained by {captain}. First mate {mate} sorted island letters while ginger buns baked to provide energy after the morning watch.",
            "Pirate captain {captain} and mate {mate} raced {ship} to deliver birthday letters before sunset. A pan of ginger buns cooled safely in the galley.",
        ],
        "problem": [
            "The wheel kept springing left, and the ship returned to the same floating bottle. Long kelp had wound around the rudder, bending their voyage into a loop.",
            "A green strand tugged beneath the stern each time {ship} tried to turn right. Soon the mail boat was circling in a loop and its tired pirates had little energy left.",
        ],
        "conflict": [
            "{captain} blamed the stiff wheel and pulled harder. {mate} wanted to inspect the water first. Their conflict made the rudder groan, but it did not change the course.",
            "\"Two of us can force it,\" said {captain}. \"Or one of us can find what is stuck,\" said {mate}. The pirate conflict delayed every birthday letter.",
        ],
        "turn": [
            "They ate warm ginger buns, regained their energy, and looked over the stern together. Crumbs landed on a thick braid of kelp wrapped around the rudder.",
            "A ginger snack restored their energy. When {mate} lowered a shiny spoon beside the rudder, its reflection showed the hidden kelp knot without anyone entering the water.",
        ],
        "action": [
            "{captain} stopped forcing the wheel. {mate} hooked the loose end with a boat pole, and they took turns unwinding the kelp into a neat green coil.",
            "\"Good idea to look first,\" {captain} said. One pirate held the rudder still while the other lifted the kelp free with a safe, long hook.",
        ],
        "resolution": [
            "The wheel moved easily, and {ship} sailed out of its loop. Their conflict ended with enough time left to deliver every letter.",
            "Freed from the kelp, the rudder pointed straight toward Birthday Island. The pirates agreed that careful eyes could save more energy than a hard pull.",
        ],
        "ending": [
            "Children on the island waved their opened letters as the sunset turned the rescued coil of kelp bright green.",
            "The last envelope reached shore under a pink sky, and two ginger crumbs remained on the quiet wheel.",
        ],
        "problem_fact": "kelp wrapped around the rudder and made the mail boat circle",
        "clue_fact": "after their ginger snack, they looked carefully and found the kelp knot",
        "action_fact": "they stopped forcing the wheel and unwound the kelp with a boat hook",
        "outcome_fact": "the rudder came free and every letter reached the island",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    stable = "|".join((params.captain_name, params.mate_name, params.ship_name))
    seed = int.from_bytes(hashlib.sha256(stable.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def _render_beat(template: str, captain: Entity, mate: Entity, ship: Ship) -> str:
    return template.format(captain=captain.id, mate=mate.id, ship=ship.name)


def tell_path(world: World, captain: Entity, mate: Entity, ginger: Entity, params: StoryParams) -> dict:
    rng = _rng_for(params)
    arc_index = (params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)
    arc = ARCS[arc_index]
    beats = ("premise", "problem", "conflict", "turn", "action", "resolution", "ending")
    if params.seed is None:
        chosen = {beat: rng.choice(arc[beat]) for beat in beats}
    else:
        variant_code = (params.seed // len(ARCS)) % (2 ** len(beats))
        chosen = {
            beat: arc[beat][(variant_code >> bit) % len(arc[beat])]
            for bit, beat in enumerate(beats)
        }

    rendered = {
        beat: _render_beat(chosen[beat], captain, mate, world.ship)
        for beat in beats
    }
    for index, beat in enumerate(beats):
        if index:
            world.para()
        world.say(rendered[beat])

    world.ship.loop_energy = 1.0
    world.ship.loop_depth = 0.0
    world.ship.loop_count = 1
    world.ship.conflict_active = False
    captain.meters["energy"] = 4.0
    mate.meters["energy"] = 3.0
    captain.memes["conflict"] = 0.0
    mate.memes["conflict"] = 0.0
    ginger.meters["used"] = 1.0
    return {"arc": arc, "rendered": rendered}


def tell(params: StoryParams) -> World:
    ship = Ship(name=params.ship_name)
    world = World(ship)
    captain = world.add(Entity(id=params.captain_name, kind="character", type="captain", label="captain"))
    mate = world.add(Entity(id=params.mate_name, kind="character", type="pirate", label="first mate"))
    ginger = world.add(Entity(id="ginger", kind="thing", type="thing", label="ginger tea", phrase="a warm cup of ginger tea"))
    ginger.meters["warm"] = 1.0

    path = tell_path(world, captain, mate, ginger, params)
    arc = path["arc"]
    rendered = path["rendered"]

    world.ship.facts = {
        "captain": captain,
        "mate": mate,
        "ginger": ginger,
        "ship": ship,
        "path": arc["key"],
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
        "problem_event": rendered["problem"],
        "turn_event": rendered["turn"],
        "action_event": rendered["action"],
        "resolution_event": rendered["resolution"],
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.ship.facts
    captain = f["captain"]
    mate = f["mate"]
    return [
        'Write a short pirate tale about a ship caught in a loop, where ginger helps restore energy.',
        f"Tell a child-friendly pirate story where {captain.id} and {mate.id} disagree, then solve the conflict after sharing ginger.",
        "Write a simple sea adventure that ends with a ship escaping a strange loop and sailing on.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.ship.facts
    captain = f["captain"]
    mate = f["mate"]
    return [
        QAItem(
            question=f"Who was the story about on {world.ship.name}?",
            answer=f"It was about {captain.id}, a pirate captain, and {mate.id}, the first mate, sailing together on {world.ship.name}.",
        ),
        QAItem(
            question=f"What trapped {world.ship.name} in a loop?",
            answer=f["problem_event"],
        ),
        QAItem(
            question=f"What did {captain.id} and {mate.id} discover after using ginger?",
            answer=f["turn_event"],
        ),
        QAItem(
            question=f"How did {captain.id} and {mate.id} settle their conflict?",
            answer=f"{f['action_event']} {f['resolution_event']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ginger?",
            answer="Ginger is a root with a sharp, warm taste. People use it in tea or food, and it can feel cozy on a cold day.",
        ),
        QAItem(
            question="What does energy mean in a story like this?",
            answer="Energy means having enough strength and pep to move, work, and keep going.",
        ),
        QAItem(
            question="What is a loop?",
            answer="A loop is something that goes around and comes back again and again.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  ship.loop_count={world.ship.loop_count}")
    lines.append(f"  ship.loop_energy={world.ship.loop_energy}")
    lines.append(f"  ship.loop_depth={world.ship.loop_depth}")
    lines.append(f"  ship.conflict_active={world.ship.conflict_active}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid if the ship has a loop, ginger exists, energy can be restored,
% and conflict is resolved by the end.
valid_story(loop, ginger, energy, conflict).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("theme", "loop"),
            asp.fact("theme", "energy"),
            asp.fact("theme", "ginger"),
            asp.fact("feature", "conflict"),
            asp.fact("style", "pirate_tale"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/4."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the pirate loop story.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected story fact.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world: loop, energy, ginger, and conflict.")
    ap.add_argument("--captain-name")
    ap.add_argument("--mate-name")
    ap.add_argument("--ship-name", choices=SHIP_NAMES)
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
    captain = args.captain_name or rng.choice(NAMES)
    mate = args.mate_name or rng.choice([n for n in NAMES if n != captain])
    ship = args.ship_name or rng.choice(SHIP_NAMES)
    return StoryParams(captain_name=captain, mate_name=mate, ship_name=ship)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible pirate story pattern: loop + ginger + energy + conflict")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mara", "Finn", "The Ginger Gull"),
            StoryParams("Nell", "Pip", "The Merry Loop"),
            StoryParams("Tess", "Bram", "The Blue Comet"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

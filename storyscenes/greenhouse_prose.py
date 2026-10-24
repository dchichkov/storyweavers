"""Scene-sized realizations of the greenhouse's inspected and enacted states."""
import random

from .capabilities.reading import Document, Statement


def render(spec, state, config, seed):
    rng = random.Random(seed)
    events = {e.action.id: e for e in state.events}
    initial = {table: {r.id: r for r in rows} for table, rows in spec.records.items()}
    rows = []

    def add(id, text, question, answer, *, actions=(), premises=(), needs=()):
        for table, key in premises:
            if key not in initial[table]:
                raise ValueError("Missing greenhouse premise")
        rows.append(Statement(id=id, text=text, focus="rae", kind=id, question=question, answer=answer,
            event_ids=tuple(events[a].id for a in actions) + tuple(f"initial/{t}/{k}" for t, k in premises),
            entity_ids=("rae",), needs=needs))

    def pick(*texts):
        return rng.choice(texts)

    if config.purpose == "water":
        wet = "drain" in events
        add("want", pick('Rae found the fern drooping over the edge of its pot. Its leaves hung low. '
            '"You cannot give up now," Rae told it. "I have been looking after you." The watering can waited on the bench.',
            'The smallest fern in the greenhouse had folded its leaves downward. Rae bent to its level. "That is not how we were going to start the morning." '
            'A watering can seemed like the obvious answer.'),
            "What problem did Rae want to solve?", "Rae wanted to help the drooping fern recover.",
            premises=(("facts", "goal"), ("plants", "fern")))
        add("look", '"More water?" Rae asked. Ivo looked at the pot. "What does the soil feel like?" '
            'Rae stopped reaching for the can and checked the soil first.',
            "What did Rae check before deciding how to help?",
            "Rae checked the fern's soil instead of watering it immediately.", actions=("inspect_fern",), needs=("want",))
        if wet:
            add("discovery", pick('The soil was already soaked. Rae drew a finger away. "But the leaves look thirsty." '
                '"The leaves cannot tell you everything," Ivo said. Rae pushed the watering can farther from the pot.',
                'Wet soil clung to Rae\'s finger. The pot had too much water, not too little. "I nearly gave you more of the trouble," Rae whispered to the fern.'),
                "Why would more water have been the wrong remedy?",
                "The inspection showed that the soil was already waterlogged. More water would not fix that problem.",
                actions=("inspect_fern",), needs=("look",))
            add("treatment", 'Rae let the extra water drain from the pot into the tray. It was a small job done slowly. '
                'The tray grew wetter while the fern\'s soil stopped being soaked. "Less," Rae said. "This time you needed less."',
                "How did Rae treat the waterlogged soil?",
                "Rae drained the excess water into the tray. The soil was no longer waterlogged afterward.", actions=("drain",), needs=("discovery",))
        else:
            add("discovery", 'The soil was dry. It crumbled instead of sticking to Rae\'s finger. "This time the can is the answer," Rae said. '
                'Ivo nodded. "Now you have asked the pot as well as the leaves."',
                "What did the soil inspection reveal?",
                "The fern's soil was dry, so it needed water.", actions=("inspect_fern",), needs=("look",))
            add("treatment", ('Rae found the can empty and filled it at the tap first. ' if "fill" in events else
                              'There was water ready in the can. ') +
                'Rae watered the dry soil. "Not a whole sea," Ivo said. Rae stopped when the soil had enough. The fern did not spring upright on command.',
                "How did Rae help the dry fern?",
                "Rae watered the dry soil with the can." + (" The empty can was filled first." if "fill" in events else " Water was already available in it."),
                actions=tuple(a for a in ("fill", "water") if a in events), needs=("discovery",))
        add("wait", 'Rae wanted to check the leaves every moment. Ivo shook his head. "It is a plant, not a button." '
            'They left it until the following morning.',
            "Did the story claim the fern recovered immediately?",
            "No. Rae left the treated plant overnight before checking it again.", actions=("night",), needs=("treatment",))
        add("ending", pick('By morning the fern had lifted its leaves. Rae crouched beside it again. "There you are." '
            'The pot was still small. The space its leaves made above it was not.',
            'The next morning, the fern was upright and recovered. Rae looked from the leaves to the soil. This time there were two places to look before reaching for the can.'),
            "What was the fern's condition the next morning?",
            "After the correct treatment and a night of waiting, the fern had recovered and lifted its leaves.", actions=("morning",), needs=("wait",))
    elif config.purpose == "support":
        supported = "support" in events
        long_enough = state.get("garden_readings", "stake").value >= state.get("plants", "fern").height
        add("want", pick('The tall fern leaned over the greenhouse bench. A draft was expected during the night. '
            '"You have grown into trouble," Rae said. Ivo brought Rae\'s attention to the spare stake.',
            'Rae liked how tall the fern had grown, until the night\'s draft was mentioned. The stem had no support. '
            '"Being the tallest is not always the easiest," Rae told it.'),
            "Why did the tall fern need help before night?",
            "The unsupported fern needed protection from the expected draft.", premises=(("facts", "goal"), ("plants", "fern")))
        add("measure", 'Rae compared the spare stake with the stem. "A stick is a stick," Ivo began. '
            '"Until it is too short," Rae said, holding them side by side.',
            "What did Rae check about the spare stake?",
            "Rae measured whether it would reach high enough to support the tall stem.", actions=("measure_stake",), needs=("want",))
        add("constraint", ('The spare stake reached high enough, and there was cord to tie it.' if supported else
            'The spare stake reached only partway up the stem. The top would still have no support.' if not long_enough else
            'The stake was long enough, but the cord supply was empty. Holding a stake beside a stem was not the same as tying it.'),
            "Could Rae use the spare stake to support the fern?",
            "Yes. The stake was long enough and cord was available." if supported else
            "No. The stake was too short to support the whole stem." if not long_enough else
            "No. The stake was long enough, but there was no cord to attach it.",
            actions=("measure_stake",), premises=(("garden_supplies", "cord"),), needs=("measure",))
        if supported:
            add("choice", pick('Rae tied the stem to the long stake. "Not too tight," Ivo said. Rae left the plant room to be a plant. '
                'When Rae let go, the stake stayed with the fern.',
                'The cord went around the stake and stem. Rae finished the tie and took both hands away. The fern no longer depended on someone standing beside it all night.'),
                "How did Rae protect the fern?",
                "Rae used cord to attach the long stake to the fern. The support remained with the plant after Rae let go.",
                actions=("support",), needs=("constraint",))
        else:
            add("choice", 'Rae looked from the tools to the sheltered corner. "Then the plant can move instead." '
                'Rae lifted the pot from the bench and put it in the corner, away from the expected draft. The shortfall in supplies did not have to become a broken stem.',
                "What alternative did Rae use when staking was not possible?",
                "Rae moved the fern from the bench to the sheltered corner. It would be protected there without an attached stake.",
                actions=("lift_fern_bench", "put_fern_shelter"), needs=("constraint",))
        add("night", 'They left the fern in its new arrangement overnight. Rae did not stand there holding it. '
            'The whole point was that the arrangement could do the waiting.',
            "Did the fern require someone to hold it through the night?",
            "No. It was left with its support in place." if supported else "No. It was left in the sheltered corner instead.",
            actions=("night",), needs=("choice",))
        add("ending", ('The next morning, the fern stood safely beside its stake. Ivo looked at the cord. "That little bit did a lot." '
                'Rae looked at the tall leaves. "It had something to hold on to."' if supported else
                'Morning found the fern safe in the corner. There was still no stake holding it. Rae smiled at the empty part of the bench. Sometimes the helpful thing was the place you did not leave a plant.'),
                "How had the fern fared by morning?",
                "It remained healthy after the night because the attached stake supported it." if supported else
                "It remained healthy in the sheltered corner, even though no stake had been attached.",
                actions=("morning",), needs=("night",))
    elif config.purpose == "light":
        late = "arrive_ivo" in events
        lamp = "lamp_ivy" in events
        add("want", pick('One bright place on the greenhouse sill. Two little plants that needed a full turn there. '
            'Rae looked at the fern, then at the narrow sill. "We shall have to arrange this." Ivo\'s ivy needed light too.',
            'The sunny sill had room for only one pot. Rae\'s fern needed two hours of bright light, and Ivo\'s ivy needed the same. '
            'Putting a larger wish in the window would not make the sill wider.'),
            "What made sharing the sunny sill difficult?",
            "Only one pot fitted on it, but the fern and ivy each needed a full two-hour light turn.",
            premises=(("facts", "goal"), ("entities", "sill"), ("plants", "fern"), ("plants", "ivy")))
        add("first", 'Rae put the fern on the sill for its two-hour turn. When its time was over, Rae lifted it down and set it back on the bench. '
            '"Finished does not mean yours forever," Rae told the fern. The bright place was empty again.',
            "How did Rae free the sill after the fern's turn?",
            "Rae gave the fern two hours of sunlight, then moved it back to the bench so another pot could use the sill.",
            actions=("put_fern_sill", "sun_fern", "put_fern_bench"), needs=("want",))
        if late:
            add("arrival", 'Ivo came in from the porch with the ivy after the fern\'s turn had ended. '
                'There was less than a full two-hour turn of daylight left. "I am late," Ivo said. "The sun noticed," Rae said, softly.',
                "Why could the ivy not receive a full turn of sunlight?",
                "Ivo arrived with it too late. Less than two hours of usable daylight remained.",
                actions=("wait_friend", "arrive_ivo", "arrive_ivy"), needs=("first",))
        else:
            add("arrival", 'Ivo\'s ivy was already waiting on the bench. Rae lifted it into the space the fern had left. '
                '"Your turn," Rae said. There was no need for the plants to squeeze together.',
                "How did the ivy get space without overcrowding the sill?",
                "Rae put it on the sill after removing the fern. The two plants used the single space in turn.",
                actions=("lift_ivy_bench", "put_ivy_sill"), needs=("first",))
        if not late:
            add("second", 'The ivy had its two hours in the sun. By the time daylight ended, both plants had had a proper turn. '
                'Ivo looked at the sill. "It was big enough after all." "For one at a time," Rae said.',
                "Did both plants receive a full light turn?",
                "Yes. The fern had the first two hours and the ivy had the next two hours.", actions=("sun_ivy",), needs=("arrival",))
        elif lamp:
            add("second", 'Rae checked the growing lamp. Its battery still had enough charge. The ivy went onto the sill, and they gave it a full turn under the lamp instead. '
                '"Borrowed sunshine," Ivo said. "Saved sunshine," Rae said. At the end of the turn, the battery was empty.',
                "How did the ivy receive enough light after arriving late?",
                "It received a full two-hour turn from the charged growing lamp. That used the remaining battery charge.",
                actions=("put_ivy_sill", "lamp_ivy"), needs=("arrival",))
        else:
            add("second", 'The growing lamp had no charge left. Rae put the ivy on the sill, but could not give it the missing full turn. '
                'Ivo stood beside the pot. "I wanted the day to wait for me." Rae left the fern on the bench. At least the ivy would keep the place by the glass.',
                "Why was the growing lamp not a solution?",
                "Its battery had no charge. The late ivy did not receive a full light turn that day.",
                actions=("put_ivy_sill",), premises=(("garden_supplies", "lamp"),), needs=("arrival",))
        add("night", 'The greenhouse grew quiet overnight. The fern stayed on the bench; the ivy had the place on the sill. '
            'They were no longer competing for the same square of wood.',
            "Where did the plants spend the night?",
            "The fern was on the bench and the ivy was on the sill.", actions=("night",), needs=("second",))
        add("ending", ('By morning, both plants were doing well. Ivo stood between the bench and the sill. "Two turns," Ivo said. '
                '"Two plants," Rae answered. The small greenhouse had made room for both.' if state.get("plants", "ivy").recovered else
                'By morning the fern was ready, but the ivy still needed its proper light turn. Its pot waited at the glass. Ivo looked at the waiting plant, not at the clock this time.'),
                "Were both plants ready the following morning?",
                "Yes. Both had received enough light and were doing well." if state.get("plants", "ivy").recovered else
                "No. The fern had enough light, but the ivy still needed its full turn.", actions=("morning",), needs=("night",))
    else:
        repaired = "mend" in events
        add("want", pick('Rae needed to water the fern, but the can was empty. "That is easy," Rae said. '
            'It was the kind of sentence that often came just before an unexpected job.',
            'The fern needed water. Rae had a can and a tap, which seemed like all the things a watering morning ought to need.'),
            "What did Rae want to do with the watering can?",
            "Rae wanted to get water to the dry fern.", premises=(("plants", "fern"), ("garden_supplies", "can")))
        add("leak", 'Rae filled the can at the tap. Before the water reached the fern, it ran out through a leak and made a puddle. '
            'Ivo looked at the floor. "That is not the plant." "I had noticed," Rae said.',
            "Where did the first canful of water go?",
            "It leaked from the can into a puddle instead of reaching the fern.", actions=("fill", "leak"), needs=("want",))
        add("diagnosis", 'Rae looked at the empty can beside the new puddle. Filling it again without changing anything would only make a larger puddle. '
            '"The fern is not drinking it," Rae said. "The can is losing it."',
            "Why was simply refilling the can not enough?",
            "The can still leaked, so another filling would lose water the same way.", actions=("leak",), needs=("leak",))
        if repaired:
            add("repair", 'There was a spare washer. Rae fitted it to stop the leak, then filled the can again. '
                'This time the water stayed inside. "Much better manners," Ivo told the can.',
                "How did Rae make the can hold water?",
                "Rae used the spare washer to repair the leak, then refilled the sound can.", actions=("mend", "refill"), needs=("diagnosis",))
        else:
            add("repair", 'There was no spare washer. Rae left the leaking can alone and looked at the jug of water on the bench. '
                '"You do not have to be called a watering can to carry water," Rae told it.',
                "What alternative did Rae choose without a spare washer?",
                "Rae used the sound jug of water instead of refilling the leaking can.", premises=(("garden_supplies", "washer"), ("garden_supplies", "jug")), needs=("diagnosis",))
        add("watering", 'Rae checked the fern\'s soil. It was dry. The water from ' + ('the repaired can' if repaired else 'the jug') +
            ' went into the pot this time, not onto the floor. Ivo watched the puddle stay exactly the same size.',
            "Did the fern finally receive water?",
            "Yes. After checking the dry soil, Rae watered it with " + ("the repaired can." if repaired else "the jug."),
            actions=("inspect_fern", "water" if repaired else "jug_water"), needs=("repair",))
        add("night", 'They left the watered fern overnight. The puddle did not need another drink, and the pot did not need another whole canful.',
            "Did Rae keep pouring water after treating the dry soil?",
            "No. Rae stopped after watering the soil and left the fern overnight.", actions=("night",), needs=("watering",))
        add("ending", ('Morning found the fern recovered and the mended can still sound. Rae looked at the leaves, then at the dry outside of the can. '
                'Two things had been helped by finding one small hole.' if repaired else
                'The fern had lifted its leaves by morning. The leaking can still needed a washer, but the jug had done the useful work. Ivo looked at it with new respect. "A watering jug," Ivo said.'),
                "What had recovered by morning, and was the can repaired?",
                "The fern had recovered, and the can's leak had been repaired." if repaired else
                "The fern had recovered after being watered with the jug. The can still leaked and needed repair.",
                actions=("morning",), needs=("night",))
    return Document(title=spec.title, statements=tuple(rows))

"""Whole dramatic beats selected from the theater's enacted changes."""
import random

from .capabilities.reading import Document, Statement


def render(spec, state, config, seed):
    rng = random.Random(seed)
    events = {e.action.id: e for e in state.events}
    initial = {t: {r.id: r for r in rs} for t, rs in spec.records.items()}
    rows = []

    def add(id, text, question, answer, *, actions=(), premises=(), needs=()):
        for t, k in premises:
            if k not in initial[t]:
                raise ValueError("Missing theater premise")
        rows.append(Statement(id=id, text=text, focus="mina", kind=id, question=question, answer=answer,
            event_ids=tuple(events[a].id for a in actions) + tuple(f"initial/{t}/{k}" for t, k in premises),
            entity_ids=("mina",), needs=needs))

    def pick(*options):
        return rng.choice(options)

    if config.purpose == "shadow":
        giant = state.get("performances", "stage").ending == "giant_shadow"
        add("want", pick('Mina wanted a friendly visitor for the little theater\'s shadow scene. Jo was behind the paper screen, arranging the lamp and a cutout. '
            '"Tell me when you are ready," Mina called. Then a very large shape appeared on the screen.',
            'The visitor in Mina\'s shadow play was supposed to be friendly. From the stage, however, the shape on the paper screen looked enormous. '
            'Jo had put a cutout close to the lamp behind it. Mina could see the shadow, but not what made it.'),
            "What surprised Mina about the projected visitor?",
            "The visitor's shadow looked enormous on the paper screen.", actions=("large_shadow", "see_large"), premises=(("performances", "stage"),))
        add("doubt", '"Jo?" Mina called. "How big is our visitor?" "Small enough for me to carry." '
            'Mina looked at the screen again. "Then you have become much stronger." Jo laughed from behind it. "Watch."',
            "Why did Jo's description puzzle Mina?",
            "Jo said the visitor was small enough to carry, but Mina was looking at an enormous shadow.",
            actions=("see_large",), needs=("want",))
        add("experiment", pick('Jo moved the paper cutout farther from the lamp. Its shadow shrank. Mina did not move closer or farther away. '
            '"It is not walking away," Mina said. "You are changing the light."',
            'The shadow became smaller as Jo moved the cutout away from the lamp. Mina watched it lose its great height without taking a step. '
            '"That would be a useful trick for a very crowded bus," Mina said.'),
            "What made the shadow smaller?",
            "Jo moved the cutout farther from the lamp. Mina saw the smaller shadow on the same screen.",
            actions=("small_shadow", "see_small"), needs=("doubt",))
        add("source", 'Mina went into the wings to look. There was no enormous visitor there: just Jo, the lamp, and a paper cutout. '
            'Mina inspected the cutout. "You have been looking much bigger than yourself," Mina told it. Jo held back a smile.',
            "What did Mina discover behind the screen?",
            "The source was a paper cutout lit by the lamp, not an enormous visitor.", actions=("backstage", "inspect_source"), needs=("experiment",))
        add("choice", ('Mina went back to the stage. "Let us keep the big shadow. A friendly visitor can be large." '
            'Jo moved the cutout close to the lamp again. The shadow grew, and this time Mina knew exactly why.' if giant else
            'Mina went back to the stage. "The smaller visitor suits this scene." Jo left the cutout farther from the lamp. '
            'There was room around the shadow now, instead of a screen filled by it.'),
            "Which shadow size did Mina choose for the scene?",
            "Mina chose the large shadow, so Jo moved the cutout close to the lamp again." if giant else
            "Mina chose the small shadow, so the cutout stayed farther from the lamp.",
            actions=("onstage", "restore_large") if giant else ("onstage",), needs=("source",))
        add("ending", pick('The scene began. Mina welcomed the visitor on the screen instead of retreating from it. '
            'The paper figure had not become any friendlier. Mina simply knew it better.',
            'When the scene began, Mina stood beside the visitor\'s shadow. "Come in," Mina said. '
            'There was still a lamp behind the screen and still a cutout. Now there was a welcome in front of it.'),
            "How did Mina treat the shadow in the finished scene?",
            "Mina welcomed it as the scene's visitor after discovering how the shadow was made.", actions=("perform",), needs=("choice",))
    elif config.purpose == "cue":
        blank = "mime" in events
        visible = "read_mina" in events
        add("want", pick('Mina stood beside the stage door. Jo was waiting in the wings to play the visitor. '
            'Mina was meant to speak a welcome, but the words had gone. The door stayed shut. "I know what happens," Mina whispered. "I cannot find what I say."',
            'The little theater had a door, a visitor waiting in the wings, and a welcome that Mina could not remember. '
            'Mina stood on the stage with an empty moment where the first line ought to be.'),
            "What stopped the welcome scene from starting?",
            "Mina could not remember the welcoming line, so Jo was still waiting in the wings.",
            premises=(("theater_players", "mina"), ("containers", "door"), ("parents", "jo")))
        add("book", ('Jo found a blank page in the prompt book, carried the book onto the stage, and put it on the reading stand. '
            'Mina inspected the page too. Not one word. Jo went back into the wings while Mina looked at the shut door.' if blank else
            'Jo read the line in the prompt book: "The door is open. Come in." It was a very short sentence to have lost. '
            'Jo leaned toward the stage to give Mina a quiet cue.'),
            "What did Jo find in the prompt book?",
            "The page was blank, so it could not supply the missing line." if blank else
            'The written line was, "The door is open. Come in."',
            actions=("read_jo", "take_book", "show_book", "place_book", "read_mina", "jo_back") if blank else ("read_jo",), needs=("want",))
        if blank:
            add("obstacle", '"We cannot read a blank page louder," Mina said. Jo looked from the book to the door. '
                '"What was the welcome meant to do?" "Let you in." Mina stopped trying to remember the shape of the sentence.',
                "Why would reading the prompt book louder not help?",
                "There were no words on the page to read. They needed another way to enact the welcome.", actions=("read_jo",), needs=("book",))
            add("solution", 'Mina decided to play the welcome without words. An open hand could invite; a step aside could make room. '
                '"You will know when to come in," Mina told Jo. This time the pause was part of a plan.',
                "What did Mina choose instead of recovering a spoken line?",
                "Mina chose a wordless welcome, using a gesture and the open doorway.", actions=("mime",), needs=("obstacle",))
        elif visible:
            add("obstacle", 'Jo whispered the line from the wings, but the noise around the stage swallowed the quiet words. '
                'Mina shook her head. "I can see that you know it. I cannot hear it." Making the same whisper twice would not make the room quiet.',
                "Why did Jo's whispered cue fail?",
                "The stage was too noisy for Mina to hear the quiet cue from the wings.", actions=("cue",), needs=("book",))
            add("solution", 'Jo carried the prompt book onto the stage and set it on the reading stand. Mina read the line there. '
                '"Ah," Mina said. "It was waiting on paper." Jo went back into the wings to be the visitor again.',
                "How did Mina recover the line despite the noise?",
                "Jo brought the book to the stage and put it on the stand. Mina could read the line instead of hearing it.",
                actions=("take_book", "show_book", "place_book", "read_mina", "jo_back"), needs=("obstacle",))
        else:
            add("obstacle", 'Mina waited by the door instead of inventing a different line. Jo whispered from the wings. '
                'The room was quiet enough for the words to reach the stage.',
                "Could Mina hear the cue from the wings?",
                "Yes. The room was quiet enough, so Mina heard the line Jo whispered.", actions=("cue",), needs=("book",))
            add("solution", 'The missing sentence came back to Mina. It did not need a grand voice. It only needed to mean what it said. '
                'Mina put a hand on the stage door, ready to make the words true.',
                "What could Mina do after hearing the cue?",
                "Mina could remember the welcome and prepare to open the door for Jo.", actions=("cue",), needs=("obstacle",))
        add("welcome", ('Mina opened the door, stepped aside, and held out a hand. Jo came onto the stage. '
            'Neither of them had needed to read a word from the blank page.' if blank else
            'Mina opened the stage door. "The door is open. Come in." This time it really was. Jo came through from the wings.'),
            "Did the visitor actually enter the scene?",
            "Yes. Mina opened the stage door and Jo came onto the stage.", actions=("open_door", "enter"), needs=("solution",))
        add("ending", ('They finished the little welcome scene without the missing line. Mina and Jo stood on the same side of the open door. '
            'The book still had a blank page. The stage no longer had an empty welcome.' if blank else
            'The welcome scene was complete. Jo looked back at the open door. "That was my cue." '
            'Mina smiled. The sentence had found its way from the book to a place where somebody could walk through it.'),
            "What showed that the welcome had succeeded?",
            "Jo had joined Mina on the stage through the open door, and they completed the scene.", actions=("perform",), needs=("welcome",))
    else:
        resized = "resize" in events
        displayed = "display_crown" in events
        failed = state.get("theater_notices", "first_fit").value == "False"
        add("want", pick('Mina was to play the ruler in the little theater. Jo\'s costume crown was ready, and the royal chair waited on the stage. '
            '"Do I look ready?" Mina asked in the wings. "Let us find out whether the crown agrees," Jo said.',
            'The ruler\'s first entrance was nearly ready: a chair on the stage, a crown in the costume tray, and Mina in the wings. '
            'Mina looked at the crown. "It seems to know its part already."'),
            "What part was Mina preparing to play?",
            "Mina was preparing to play the ruler, with a crown and a royal chair.", premises=(("performances", "stage"), ("parents", "crown"), ("parents", "chair")))
        add("fitting", ('Mina tried the crown. It was too large, slipped off, and landed back in the costume tray. '
            '"It would like a different ruler," Mina said. "It would like a smaller opening," Jo said.' if failed else
            'Mina tried the crown. It fitted and stayed in place when Mina took both hands away. '
            '"So far," Jo said, "a very steady reign." Mina tried not to smile too widely.'),
            "What happened when Mina first tried the crown?",
            "It was too large and slipped back into the costume tray." if failed else
            "It fitted Mina and stayed in place.", actions=("try_crown",), needs=("want",))
        add("constraint", ('There was a fastening clip in the tray. Jo pointed to the crown\'s adjustable band. '
            '"The ruler can stay the same size," Jo said. "The costume is the part we can change."' if resized else
            'The fastening clip was missing. Mina could not make the crown fit by wishing for it. '
            'On the stage, the royal chair was still waiting.' if displayed else
            'Mina reached to hold the crown anyway. "You have already checked it," Jo said. '
            'Mina lowered both hands. There would be room to act a part, not just keep a costume on.'),
            "What limited or enabled Mina's next choice?",
            "The available clip could fasten the adjustable crown more tightly." if resized else
            "No fastening clip was available, so the oversized crown could not be tightened." if displayed else
            "The crown already fitted, so Mina did not need to keep holding it.",
            actions=("try_crown",), premises=(("theater_props", "clip"),), needs=("fitting",))
        add("choice", ('Mina narrowed the band and fastened it with the clip, then tried the crown again. It stayed on. '
            '"Same ruler?" Jo asked. "Better hat," Mina said.' if resized else
            'Mina picked up the crown. "It can be royal without being on my head." Mina carried it onto the stage and placed it on the royal chair. '
            'The crown had a place in the scene; it did not have to wear Mina.' if displayed else
            'Mina walked onto the stage wearing the fitted crown. There was nothing to fix. '
            'That left the more interesting problem of what kind of ruler to be.'),
            "How did Mina arrange the crown for the scene?",
            "Mina tightened it with the clip and tried it again; it now fitted." if resized else
            "Mina carried it onto the stage and displayed it on the royal chair instead of wearing it." if displayed else
            "Mina wore the already-fitted crown onto the stage.",
            actions=("resize", "retry_crown") if resized else ("carry_crown", "onstage", "display_crown") if displayed else ("onstage",), needs=("constraint",))
        add("entrance", ('Mina came onto the stage with the crown secure. Both hands were free for the welcome.' if resized else
            'Mina stood beside the crowned chair, bareheaded. Both hands were free for the welcome.' if displayed else
            'Mina stood beside the royal chair. The crown stayed where it belonged without a hand checking it.') +
            ' "Welcome," Mina said, and gave a proper bow.',
            "Was Mina able to perform the entrance?",
            "Yes. Mina performed on stage with the crown displayed on the chair." if displayed else
            "Yes. Mina performed on stage wearing the fitted crown.", actions=("perform",), needs=("choice",))
        add("ending", ('The crown shone on the chair while Mina finished the scene. "Nobody will mistake the chair for the ruler," Jo said. '
            'Mina bowed again. "I hope not. It has not learned any lines."' if displayed else
            'Mina finished the scene without catching the crown once. Jo looked pleased. '
            'The small gold circle had stopped being the whole performance and become one part of it.'),
            "Where was the crown when the scene ended?",
            "It was on the royal chair, while Mina performed bareheaded." if displayed else
            "It was still fitted on Mina's head at the end of the scene.", actions=("perform",), needs=("entrance",))
    return Document(title=spec.title, statements=tuple(rows))

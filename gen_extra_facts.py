#!/usr/bin/env python3
"""Generate extra_facts_31_395.json — 3 supplemental facts per topic 31-395."""

import json
from pathlib import Path

OUTPUT = Path("/workspace/extra_facts_31_395.json")

# 365 entries (topics 31-395), each a list of 3 full-sentence facts
EXTRAS = [
    ["The Great Pyramid of Giza originally stood 481 feet tall and was the world's tallest structure for nearly 4,000 years.", "Archaeologists believe a skilled workforce of thousands — not slaves — built the pyramids over roughly 20 years.", "The pyramids were designed as elaborate tombs to ensure the pharaoh's safe passage to the afterlife."],
    ["Hammurabi was the sixth king of Babylon and ruled from approximately 1792 to 1750 BCE.", "The code included detailed laws on trade, family, property, and criminal punishment.", "Its principle of proportional justice influenced legal systems across the ancient Near East."],
    ["The Spartan stand at Thermopylae bought critical time for Greece to organize its defenses.", "The Greek historian Herodotus recorded the battle, blending history with enduring legend.", "A monument at the site honors the Spartans who obeyed their laws and stayed to fight."],
    ["Alexander was tutored by Aristotle and carried a copy of the Iliad on his campaigns.", "He founded Alexandria in Egypt, which became a great center of learning and culture.", "His vast empire fragmented into rival Hellenistic kingdoms after his death at age 32."],
    ["Caesar's dictatorship for life alarmed senators who feared the return of monarchy.", "Marc Antony's funeral speech turned public opinion against the assassins.", "Caesar's heir Octavian eventually defeated his killers and became Emperor Augustus."],
    ["Rome's fall was a gradual process of economic decline, military pressure, and political instability.", "The sack of Rome by Visigoths in 410 CE shocked the ancient world.", "The Eastern Roman Empire at Constantinople survived for another thousand years."],
    ["Spartacus was a former gladiator who became the most feared rebel leader in Roman history.", "The revolt threatened Rome's entire social order built on slavery.", "Crassus and Pompey ultimately crushed the rebellion and claimed the glory."],
    ["Cleopatra was the last pharaoh of Egypt and a shrewd political strategist.", "She aligned Egypt with Rome through relationships with Caesar and Mark Antony.", "After her defeat, Egypt became a province of the Roman Empire."],
    ["Hannibal's crossing of the Alps with war elephants remains one of history's boldest military maneuvers.", "At Cannae he destroyed a Roman army nearly twice the size of his own.", "Scipio Africanus finally defeated Hannibal at the Battle of Zama in 202 BCE."],
    ["Homer's Iliad and Odyssey immortalized the Trojan War for Western civilization.", "Archaeologist Heinrich Schliemann excavated Troy in the 1870s.", "The war symbolizes the blurred line between ancient myth and historical memory."],
    ["Socrates was charged with impiety and corrupting the youth of Athens.", "He chose to drink hemlock rather than accept exile from his beloved city.", "His student Plato preserved his teachings, shaping Western philosophy forever."],
    ["The terracotta warriors were buried to protect Qin Shi Huang in the afterlife.", "An estimated 8,000 life-sized figures have been discovered so far.", "The site near Xi'an remains one of the greatest archaeological finds of the 20th century."],
    ["The Great Wall was built and rebuilt by multiple Chinese dynasties over centuries.", "It stretches over 13,000 miles across northern China's rugged terrain.", "Today it stands as a UNESCO World Heritage Site and symbol of Chinese civilization."],
    ["The Silk Road connected merchants, monks, and travelers across thousands of miles.", "Paper, gunpowder, and Buddhism spread along its ancient trade routes.", "Marco Polo's travels along the Silk Road opened European eyes to Asia's riches."],
    ["The Maya built sophisticated cities with pyramids, observatories, and advanced calendars.", "Their writing system was the most developed in the pre-Columbian Americas.", "The Classic Maya collapse around 900 CE remains one of archaeology's great mysteries."],
    ["Tenochtitlan was one of the largest cities in the world when the Spanish arrived.", "Aztec engineers built canals, causeways, and floating gardens on a lake.", "Spanish conquest and European diseases devastated the Aztec population within decades."],
    ["The Inca ruled an empire of roughly 10 million people without a written language.", "They built Machu Picchu and an extensive road network high in the Andes.", "Spanish conquistadors captured the Inca emperor Atahualpa and seized their gold."],
    ["Stonehenge was built in stages between 3000 and 2000 BCE on England's Salisbury Plain.", "Some bluestones were transported over 150 miles from Wales.", "The monument aligns with the summer and winter solstices."],
    ["The Rosetta Stone was the key that unlocked the mystery of Egyptian hieroglyphics.", "It bears the same decree written in hieroglyphic, demotic, and Greek scripts.", "Jean-François Champollion cracked the code in 1822 after years of study."],
    ["Mount Vesuvius erupted on August 24, 79 CE, burying Pompeii under volcanic ash.", "The ash preserved buildings, artifacts, and haunting body casts for centuries.", "Pompeii was rediscovered in 1748 and offers a frozen snapshot of Roman daily life."],
]

def main():
    if len(EXTRAS) != 365:
        raise SystemExit(f"Expected 365 extra-fact sets, got {len(EXTRAS)}")
    data = {str(31 + i): facts for i, facts in enumerate(EXTRAS)}
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(data)} topic extras to {OUTPUT}")


if __name__ == "__main__":
    main()

const ARTICLES = [
  "rue", "avenue", "boulevard", "chemin", "place", "allée", "impasse", "passage",
  "la", "le", "les", "de", "du", "des", "l'",
  "der", "die", "das", "am", "an", "im", "zum",
  "the", "of",
];

const SUFFIX_WORDS = ["straße", "strasse", "gasse", "weg", "platz", "ring", "allee"];

function transliterate(str) {
  return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function extractStreet3(streetName) {
  const words = transliterate(streetName)
    .replace(/[^a-zA-Z\s]/g, "")
    .split(/\s+/)
    .filter(Boolean);

  let significant = words.find(
    (w) => !ARTICLES.includes(w.toLowerCase())
  );
  if (!significant) significant = words[0] || "";

  for (const suffix of SUFFIX_WORDS) {
    const lower = significant.toLowerCase();
    if (lower.endsWith(suffix) && lower.length > suffix.length) {
      significant = significant.slice(0, -suffix.length);
      break;
    }
  }

  return significant.slice(0, 3).toUpperCase();
}

function extractNumber(streetNumber) {
  const match = String(streetNumber || "").match(/\d+/);
  return match ? match[0] : "0";
}

export function generateSmartHomeId({ country, postalCode, streetName, streetNumber, suffix }) {
  const c = (country || "XX").toUpperCase().slice(0, 2);
  const zip = transliterate(String(postalCode || "00000"))
    .replace(/\s/g, "")
    .toUpperCase()
    .slice(0, 10);
  const street3 = extractStreet3(streetName || "UNK");
  const num = extractNumber(streetNumber);
  const nn = String(suffix || 1).padStart(2, "0");

  return `${c}-${zip}-${street3}${num}-${nn}`;
}

export function parseSmartHomeId(id) {
  const parts = id.split("-");
  if (parts.length < 4) return null;
  const country = parts[0];
  const zip = parts[1];
  const streetNum = parts[2];
  const nn = parts[3];
  return { country, zip, streetNum, suffix: parseInt(nn, 10) };
}

// 1. (Headword, Num, Pronunciation + label)
document.querySelectorAll("div").forEach((div) => {
  let p = div.querySelector("p");
  if (!p) return;


  if (!p.firstChild || p.firstChild.nodeType !== Node.TEXT_NODE) return;

  let text = p.firstChild.textContent;
  
  let headerMatch = text.match(/^([^\s\d(<]+)(?:\s+(\d+))?(?:\s+(\([^)]+\)))?\s*/);

  if (headerMatch) {
    let fullHeaderString = headerMatch[0]; 
    let headword = headerMatch[1];
    let superNum = headerMatch[2] || "";
    let syllables = headerMatch[3] || "";

    let bodyHTML = p.innerHTML.replace(fullHeaderString, "").trim();

    let tempDiv = document.createElement("div");
    tempDiv.innerHTML = bodyHTML;
    let cleanText = tempDiv.textContent.trim();

    let contentHTML = "";

    if (cleanText.endsWith("]") && !cleanText.endsWith(")")) {
        let lastBracketIndex = bodyHTML.lastIndexOf("[");
        if (lastBracketIndex !== -1) {
            let mainPart = bodyHTML.substring(0, lastBracketIndex).trim();
            let labelPart = bodyHTML.substring(lastBracketIndex).trim();
            
            contentHTML = `<span class="pos">${mainPart}</span>` + 
                          `<div class="domain-label">${labelPart}</div>`;
        } else {
            contentHTML = `<span class="pos">${bodyHTML}</span>`;
        }
    } else {
        contentHTML = `<span class="pos">${bodyHTML}</span>`;
    }

    let headerHTML = `<div class="header-row"><span class="headword">${headword}</span>`;
    if (superNum) headerHTML += `<sup class="head-num">${superNum}</sup>`;
    if (syllables) headerHTML += ` <span class="syllables">${syllables}</span>`;
    headerHTML += `</div>`;

    p.innerHTML = headerHTML + `<div class="content-row">${contentHTML}</div>`;
    
    p.classList.add("processed-header");
  }
});

// BULLET POINTS 
document.querySelectorAll("li, section:not(.origin_block)").forEach((el) => {
  if (el.innerHTML.includes("•") && !el.querySelector(".sub-sense")) {
    const parts = el.innerHTML.split("•");
    let newHTML = parts[0];
    for (let i = 1; i < parts.length; i++) {
      let content = parts[i].trim();
      if (content) {
        newHTML += `<div class="sub-sense">• ${content}</div>`;
      }
    }
    el.innerHTML = newHTML;
  }
});

// 3. DATA/ETIMOLOGIA
document.querySelectorAll(".origin_block").forEach((sec) => {
  sec.innerHTML = sec.innerHTML.replace(/\bDATA\b/g, "\nDATA");
});

// 4. SQUARE BRACKETS 
document.querySelectorAll("li, p, section").forEach((el) => {
  if (el.querySelector(".header-row") || el.classList.contains("processed-header")) return;

  if (el.innerHTML.includes("[")) {
    el.innerHTML = el.innerHTML.replace(
      /\[([^\]]+)\]/g,
      '<span class="domain-label">[$1]</span>'
    );
  }
});

// 5. SUPERSCRIPT 
document.querySelectorAll("ul, .origin_block").forEach((el) => {
  el.innerHTML = el.innerHTML.replace(
    /([a-zA-Z\u00C0-\u017F]+)(\d+)(?![^<]*>)/g,
    "$1<sup>$2</sup>"
  );
});

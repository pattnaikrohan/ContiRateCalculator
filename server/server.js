import express from 'express';
import cors from 'cors';
import { TARIFF, MINE_KEYS, PERTH_METRO, FUEL_SURCHARGE, findRow } from './data/tariffData.js';

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

app.post('/api/calculate', (req, res) => {
  try {
    const { origin, dest, weight, reels, dimL, dimW, dimH, gst } = req.body;

    const weightRaw = parseFloat(weight);
    const numReels = parseInt(reels) || 1;
    const L = parseFloat(dimL);
    const W = parseFloat(dimW);
    const H = parseFloat(dimH);

    if (!dest || isNaN(weightRaw) || weightRaw <= 0) {
      return res.status(400).json({ error: 'Invalid weight or destination' });
    }

    let cbmPerReel = null;
    let frtBasis = weightRaw;
    let basisLabel = `${weightRaw}T (weight)`;

    if (!isNaN(L) && !isNaN(W) && !isNaN(H) && L > 0 && W > 0 && H > 0) {
      cbmPerReel = (L / 100) * (W / 100) * (H / 100);
      if (cbmPerReel > weightRaw) {
        frtBasis = cbmPerReel;
        basisLabel = `${cbmPerReel.toFixed(3)} CBM (greater than ${weightRaw}T)`;
      } else {
        basisLabel = `${weightRaw}T (greater than ${cbmPerReel.toFixed(3)} CBM)`;
      }
    }

    const row = findRow(frtBasis);
    const rowW = findRow(weightRaw);
    const isMine = MINE_KEYS[dest] !== undefined;
    const isMetro = PERTH_METRO[dest] !== undefined;
    const isPerthDest = isMine || isMetro || dest === 'seafreight';

    let lines = [];
    let total = 0;

    const melCart = rowW.melCart * numReels;
    lines.push({ label: 'Melbourne cartage', value: melCart });
    total += melCart;

    if (weightRaw > 30) {
      const craneMel = 1975 * numReels;
      lines.push({ label: 'Melbourne crane lift (avg. assumption, >30T)', value: craneMel, crane: true });
      total += craneMel;
    }

    const seafrtCalc = frtBasis * row.combined * numReels;
    lines.push({ label: `Sea freight — ${basisLabel} × $${row.combined}/FRT`, value: seafrtCalc });
    total += seafrtCalc;

    if (isPerthDest) {
      const fremCraneRate = weightRaw < 38 ? 500 : 700;
      const fremCrane = fremCraneRate * numReels;
      lines.push({ label: `Fremantle crane (${weightRaw < 38 ? '<38T @ $500' : '≥38T @ $700'} per reel)`, value: fremCrane, crane: true });
      total += fremCrane;
    }

    if (isMetro || isMine) {
      const mkey = isMetro ? PERTH_METRO[dest] : MINE_KEYS[dest];
      const baseTransport = rowW.mineRates[mkey] * numReels;
      const fuelAmt = baseTransport * FUEL_SURCHARGE;
      const destLabel = isMetro ? 'Perth metro transport (base rate)' : 'Mine site transport (base rate)';

      lines.push({ label: destLabel, value: baseTransport });
      total += baseTransport;

      lines.push({ label: 'Fuel surcharge (38% of transport)', value: fuelAmt, fuel: true });
      total += fuelAmt;

      const wpCost = 400 * numReels;
      lines.push({ label: 'Western Power permit ($400 per reel)', value: wpCost });
      total += wpCost;

      const portFee = 50 * numReels;
      lines.push({ label: 'Port booking fee ($50 per reel)', value: portFee });
      total += portFee;
    }

    if (gst) {
      const gstAmt = total * 0.10;
      lines.push({ label: 'GST (10%)', value: gstAmt, muted: true });
      total += gstAmt;
    }

    res.json({
      success: true,
      lines,
      total,
      reels: numReels,
      weightRaw,
      basisLabel,
      demurr: rowW.demurr
    });

  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error during calculation' });
  }
});

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});

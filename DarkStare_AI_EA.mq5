//+------------------------------------------------------------------+
//| DarkStare AI Signal Reader EA v2.0                               |
//| Reads live AI signals from DarkStare AI Trading Brain            |
//+------------------------------------------------------------------+
#property copyright "DarkStare AI v2.0"
#property version   "2.0"
#include <Trade/Trade.mqh>

input double LotSize       = 0.01;
input int    MinConfidence = 60;
input bool   UseAILevels   = true;
input int    FallbackSL    = 300;
input int    FallbackTP    = 600;
input int    MaxPositions  = 1;
input bool   VerboseLog    = true;

CTrade trade;

string Field(string raw, string key){
   int p = StringFind(raw, key + ":");
   if(p < 0) return "";
   p += StringLen(key) + 1;
   int e = StringFind(raw, "|", p);
   return StringSubstr(raw, p, e < 0 ? StringLen(raw) - p : e - p);
}

string ReadSignal(){
   int f = FileOpen("darkstare_signal.txt", FILE_READ|FILE_TXT|FILE_COMMON);
   if(f == INVALID_HANDLE)
      f = FileOpen("darkstare_signal.txt", FILE_READ|FILE_TXT);
   if(f == INVALID_HANDLE) return "SIGNAL:NONE";
   string s = FileReadString(f);
   FileClose(f);
   return s;
}

void ClearSignal(){
   int f = FileOpen("darkstare_signal.txt", FILE_WRITE|FILE_TXT|FILE_COMMON);
   if(f == INVALID_HANDLE)
      f = FileOpen("darkstare_signal.txt", FILE_WRITE|FILE_TXT);
   if(f != INVALID_HANDLE){ FileWriteString(f, "SIGNAL:NONE"); FileClose(f); }
}

void OnTick(){
   if(PositionsTotal() >= MaxPositions) return;
   string raw  = ReadSignal();
   string act  = Field(raw, "SIGNAL");
   int    conf = (int)StringToInteger(Field(raw, "CONF"));
   if(act != "BUY" && act != "SELL") return;
   if(conf < MinConfidence){ if(VerboseLog) PrintFormat("[DarkStare] Confidence %d%% < min %d%% — skip", conf, MinConfidence); return; }
   string pair = Field(raw, "PAIR");
   if(pair != "" && pair != _Symbol){ if(VerboseLog) PrintFormat("[DarkStare] Signal for %s, EA on %s — skip", pair, _Symbol); return; }
   double ask    = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid    = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double sl_ai  = StringToDouble(Field(raw, "SL"));
   double tp_ai  = StringToDouble(Field(raw, "TP"));
   double sl = UseAILevels && sl_ai > 0 ? sl_ai : (act=="BUY" ? ask - FallbackSL*_Point : bid + FallbackSL*_Point);
   double tp = UseAILevels && tp_ai > 0 ? tp_ai : (act=="BUY" ? ask + FallbackTP*_Point : bid - FallbackTP*_Point);
   if(VerboseLog) PrintFormat("[DarkStare] %s | Conf:%d%% | Entry:~%s | SL:%.5f | TP:%.5f", act, conf, Field(raw,"ENTRY"), sl, tp);
   bool ok = false;
   if(act == "BUY")  ok = trade.Buy(LotSize, _Symbol, ask, sl, tp, "DarkStare AI");
   if(act == "SELL") ok = trade.Sell(LotSize, _Symbol, bid, sl, tp, "DarkStare AI");
   if(ok){ Print("[DarkStare] ✓ Order placed successfully"); ClearSignal(); }
   else   PrintFormat("[DarkStare] ✗ Order failed: error %d", GetLastError());
}

void OnTimer(){ OnTick(); }

int OnInit(){
   EventSetTimer(5);
   Print("═══════════════════════════════════════");
   Print("  DarkStare AI Signal Reader EA v2.0   ");
   PrintFormat("  Symbol: %s | Min Conf: %d%%", _Symbol, MinConfidence);
   PrintFormat("  Lot: %.2f | SL: %d | TP: %d pts", LotSize, FallbackSL, FallbackTP);
   Print("═══════════════════════════════════════");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason){
   EventKillTimer();
   Print("[DarkStare] EA stopped.");
}

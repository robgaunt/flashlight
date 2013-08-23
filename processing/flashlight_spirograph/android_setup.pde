//import android.content.Context;
//import android.os.PowerManager;
//import android.net.wifi.WifiManager;
//
///**
// * Helper class to do various android setup crap.
// */
//class AndroidSetup {
//  PowerManager powerManager;
//  PowerManager.WakeLock wakeLock;
//  WifiManager wifiManager;
//  WifiManager.MulticastLock multicastLock;
//
//  public AndroidSetup() {
//    Context context = getApplicationContext();
//    powerManager = (PowerManager)context.getSystemService(Context.POWER_SERVICE);
//    wifiManager = (WifiManager)context.getSystemService(Context.WIFI_SERVICE);
//  }
//
//  public void acquireLocks() {
//    wakeLock = powerManager.newWakeLock(
//        PowerManager.SCREEN_DIM_WAKE_LOCK, "flashlight.processing");
//    wakeLock.acquire();  
//    multicastLock = wifiManager.createMulticastLock("flashlight.processing");
//    multicastLock.acquire();
//  }
//  
//  public void releaseLocks() {
//    wakeLock.release();
//    multicastLock.release();
//  }
//}


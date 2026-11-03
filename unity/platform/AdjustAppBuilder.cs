using System;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;

// copied into the generated project by unity.py, which runs it with -executeMethod AdjustAppBuilder.Build
public static class AdjustAppBuilder
{
    public static void Build()
    {
        var target = EditorUserBuildSettings.activeBuildTarget;
        var namedTarget = NamedBuildTarget.FromBuildTargetGroup(BuildPipeline.GetBuildTargetGroup(target));
        PlayerSettings.SetApplicationIdentifier(namedTarget, Argument("-adjustPackage"));

        if (target == BuildTarget.Android)
        {
            // Mono cannot build for 64-bit only devices
            PlayerSettings.SetScriptingBackend(namedTarget, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;

            // EDM4U does not resolve on its own in batch mode, so do what Force Resolve does
            var resolver = AppDomain.CurrentDomain.GetAssemblies()
                .Select(assembly => assembly.GetType("GooglePlayServices.PlayServicesResolver"))
                .First(type => type != null);
            if (!(bool)resolver.GetMethod("ResolveSync", new[] { typeof(bool) }).Invoke(null, new object[] { true }))
            {
                EditorApplication.Exit(1);
            }
        }
        else if (target == BuildTarget.iOS)
        {
            // a new project gets default Adjust settings, which link AdSupport only
            AdjustSdk.AdjustSettings.iOSFrameworkAdServices = true;
            AdjustSdk.AdjustSettings.iOSFrameworkAppTrackingTransparency = true;
            AdjustSdk.AdjustSettings.iOSFrameworkStoreKit = true;
            AdjustSdk.AdjustSettings.iOSUserTrackingUsageDescription = "Adjust test app";
        }

        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
        {
            scenes = new[] { Argument("-adjustScene") },
            locationPathName = Argument("-adjustOutput"),
            target = target,
            options = Argument("-adjustMode") == "debug" ? BuildOptions.Development : BuildOptions.None
        });
        EditorApplication.Exit(report.summary.result == BuildResult.Succeeded ? 0 : 1);
    }

    private static string Argument(string name)
    {
        var args = Environment.GetCommandLineArgs();
        return args[Array.IndexOf(args, name) + 1];
    }
}

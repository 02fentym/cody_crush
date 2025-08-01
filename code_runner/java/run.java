import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;

public class Run {

    private static final Path TEST_DIR = Paths.get("tests");
    private static final Path CLASS_DIR = Paths.get("classes");
    private static final Path STUDENT_DIR = Paths.get("student");
    private static final int EXECUTION_TIMEOUT_SECONDS = 2;

    // Extracts the public class name from a Java file
    private static String findPublicClassName(Path javaFile) throws IOException {
        for (String line : Files.readAllLines(javaFile)) {
            line = line.trim();
            if (line.startsWith("public class")) {
                String[] tokens = line.split("\\s+");
                if (tokens.length >= 3) {
                    return tokens[2].replace("{", "").trim();
                }
            }
        }
        throw new IOException("No public class found in " + javaFile.getFileName());
    }

    // Detects package declaration
    private static String findPackageName(Path javaFile) throws IOException {
        try (BufferedReader br = Files.newBufferedReader(javaFile)) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith("package ")) {
                    return line.replace("package ", "").replace(";", "").trim() + ".";
                }
            }
        }
        return "";
    }

    // Compiles the Java file
    private static String compileJavaFile(Path javaFile, Path classDir) throws IOException, InterruptedException {
        classDir.toFile().mkdirs();
        ProcessBuilder pb = new ProcessBuilder("javac", "-d", classDir.toString(), javaFile.toString());
        pb.redirectErrorStream(true);
        Process process = pb.start();
        String output = new String(process.getInputStream().readAllBytes()).trim();
        if (process.waitFor(10, TimeUnit.SECONDS) && process.exitValue() != 0) {
            return output.isEmpty() ? "Compilation failed" : output;
        }
        return null; // Success
    }

    // Runs a test case and returns the result
    private static Map<String, Object> runTestCase(Path inFile, Path outFile, String className, String packageName, Path classDir) {
        Map<String, Object> result = new HashMap<>();
        String testName = inFile.getFileName().toString().replace(".in", "");
        result.put("test", testName);

        try {
            String input = Files.readString(inFile).trim();
            String expected = outFile.toFile().exists() ? Files.readString(outFile).trim() : "";

            ProcessBuilder pb = new ProcessBuilder("java", "-cp", classDir.toString(), packageName + className);
            pb.redirectErrorStream(false); // Separate error stream for clarity
            Process process = pb.start();

            // Write input to process
            try (OutputStream stdin = process.getOutputStream()) {
                stdin.write(input.getBytes());
                stdin.flush();
            }

            // Read output and error
            String actual = new String(process.getInputStream().readAllBytes()).trim();
            String error = new String(process.getErrorStream().readAllBytes()).trim();

            // Check timeout
            if (!process.waitFor(EXECUTION_TIMEOUT_SECONDS, TimeUnit.SECONDS)) {
                process.destroy();
                throw new TimeoutException("Execution timed out");
            }

            boolean passed = actual.equals(expected);
            result.put("passed", passed);
            result.put("expected", expected);
            result.put("actual", actual);
            result.put("error", error);

        } catch (IOException | InterruptedException | TimeoutException e) {
            result.put("passed", false);
            result.put("expected", outFile.toFile().exists() ? Files.readString(outFile).trim() : "");
            result.put("actual", "");
            result.put("error", e.getMessage());
        }

        return result;
    }

    // Outputs results as JSON
    private static void outputResults(List<Map<String, Object>> results, int passed) {
        Map<String, Object> summary = new HashMap<>();
        summary.put("passed", passed);
        summary.put("total", results.size());
        summary.put("all_passed", passed == results.size());

        Map<String, Object> output = new HashMap<>();
        output.put("results", results);
        output.put("summary", summary);

        System.out.println(new com.google.gson.Gson().toJson(output));
    }

    // Outputs error as JSON
    private static void outputError(String error, List<Map<String, Object>> results) {
        Map<String, Object> summary = new HashMap<>();
        summary.put("passed", 0);
        summary.put("total", results.size());
        summary.put("all_passed", false);

        Map<String, Object> output = new HashMap<>();
        output.put("results", results);
        output.put("summary", summary);
        output.put("error", error);

        System.out.println(new com.google.gson.Gson().toJson(output));
    }

    public static void main(String[] args) {
        List<Map<String, Object>> results = new ArrayList<>();

        // Find student Java file
        Path javaFile = Arrays.stream(STUDENT_DIR.toFile().listFiles((dir, name) -> name.endsWith(".java")))
                .findFirst()
                .map(File::toPath)
                .orElse(null);

        if (javaFile == null) {
            outputError("No Java file found in student directory", results);
            return;
        }

        // Extract class and package names
        String className;
        String packageName;
        try {
            className = findPublicClassName(javaFile);
            packageName = findPackageName(javaFile);
        } catch (IOException e) {
            outputError("Failed to parse Java file: " + e.getMessage(), results);
            return;
        }

        // Compile the Java file
        try {
            String compileError = compileJavaFile(javaFile, CLASS_DIR);
            if (compileError != null) {
                outputError("Compilation failed: " + compileError.replace("\"", "\\\""), results);
                return;
            }
        } catch (IOException | InterruptedException e) {
            outputError("Compilation error: " + e.getMessage().replace("\"", "\\\""), results);
            return;
        }

        // Security: Apply SecurityManager or Docker restrictions here
        // Example: System.setSecurityManager(new SecurityManager());
        // Docker: Limit CPU, memory, and network access

        // Run test cases
        File[] inputFiles = TEST_DIR.toFile().listFiles((dir, name) -> name.endsWith(".in"));
        if (inputFiles == null || inputFiles.length == 0) {
            outputError("No test input files found", results);
            return;
        }

        Arrays.sort(inputFiles, Comparator.comparing(File::getName));
        int passed = 0;

        for (File inFile : inputFiles) {
            Path outFile = TEST_DIR.resolve(inFile.getName().replace(".in", ".out"));
            Map<String, Object> result = runTestCase(inFile.toPath(), outFile, className, packageName, CLASS_DIR);
            if ((boolean) result.get("passed")) {
                passed++;
            }
            results.add(result);
        }

        outputResults(results, passed);
    }
}
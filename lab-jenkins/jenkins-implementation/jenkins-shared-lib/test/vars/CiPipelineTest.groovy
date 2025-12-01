// test/vars/CiPipelineTest.groovy
import com.lesfurets.jenkins.unit.BasePipelineTest
import org.junit.Before
import org.junit.Test

class CiPipelineTest extends BasePipelineTest {

    @Before
    void setUp() {
        super.setUp()
        // Register shared library methods
        helper.registerAllowedMethod("checkout", [Map.class], null)
        helper.registerAllowedMethod("sh", [String.class], null)
        helper.registerAllowedMethod("junit", [String.class], null)
        helper.registerAllowedMethod("cleanWs", [], null)
        helper.registerAllowedMethod("timestamps", [], null)
        
        // Mock docker global variable
        binding.setVariable('docker', [
            build: { String tag -> 
                return [ push: { String t -> println "Pushing $t" } ] 
            }
        ])
    }

    @Test
    void should_execute_maven_pipeline() {
        def script = loadScript("vars/ciPipeline.groovy")
        script.call(type: 'maven')
        
        printCallStack()
        assertJobStatusSuccess()
    }

    @Test
    void should_execute_npm_pipeline() {
        def script = loadScript("vars/ciPipeline.groovy")
        script.call(type: 'npm')
        
        printCallStack()
        assertJobStatusSuccess()
    }
}

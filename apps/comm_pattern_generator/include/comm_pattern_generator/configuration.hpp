#ifndef COMM_PATTERN_GENERATOR_CONFIGURATION_H
#define COMM_PATTERN_GENERATOR_CONFIGURATION_H

// STL
#include <vector>
#include <string>

// Boost
#include "boost/serialization/access.hpp"
#include "boost/serialization/vector.hpp" 
#include "boost/serialization/string.hpp" 

// Internal
#include "comm_pattern.hpp"

class Configuration
{
public:
  Configuration( const std::string config_file_path );
  Configuration();
  Configuration& operator=(const Configuration& rhs );
  std::vector<CommPattern> get_comm_pattern_seq() const;
  void print() const;
private:
  std::vector<CommPattern> comm_pattern_seq;
  
  // Serialization helper for broadcast 
  friend class boost::serialization::access;
  template<typename Archive>
  void serialize( Archive& archive, const unsigned int version )
  {
    archive & comm_pattern_seq;
  }
};

void broadcast_config( Configuration& config );

#endif
